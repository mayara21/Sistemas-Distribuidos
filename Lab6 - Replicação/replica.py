import socket as sock
import sys
import select
import threading
from enum import Enum
import struct

ENCODING = 'utf-8'
MAX_MESSAGE_SIZE_RECV = 4096

# auxiliary classes
class Method(Enum):
    NEW_CONNECTION = 'CON'
    UPDATE_VALUE = 'NEW'
    ANNOUNCE_PRIMARY = 'PRI'
    REQUEST_WRITE = 'WRI'

class Status(Enum):
    OK = 0
    ERROR = 1

# message mapping functions
def _pack_request_write(id):
    method_bytes = _pack_method(Method.REQUEST_WRITE.value)
    id_bytes = _pack_id(id)

    return method_bytes + id_bytes

def _pack_announce_primary(id):
    method_bytes = _pack_method(Method.ANNOUNCE_PRIMARY.value)
    id_bytes = _pack_id(id)

    return method_bytes + id_bytes

def _pack_update_value(id, value):
    method_bytes = _pack_method(Method.UPDATE_VALUE.value)
    id_bytes = _pack_id(id)
    value_bytes = _pack_value(value)

    return method_bytes + id_bytes + value_bytes

def _pack_status(status: int):
    return struct.pack('!B', status)

def _pack_method(method: str):
    return struct.pack('!3s', method.encode(ENCODING))

def _pack_id(id: int):
    return struct.pack('!B', id)

def _pack_value(value: int):
    return struct.pack('!i', value)

def _unpack_update_value(message):
    id = _unpack_id(message)
    value = _unpack_value(message[1:])

    return id, value

def _unpack_method(message: bytearray):
    return str(struct.unpack('!3s', message[:3])[0], encoding=ENCODING).strip('\x00')

def _unpack_status(message):
    return int(struct.unpack('!B', message[:1])[0])

def _unpack_id(message):
    return int(struct.unpack('!B', message[:1])[0])

def _unpack_value(message):
    return int(struct.unpack('!i', message[:4])[0])


class Replica:
    ip: str = 'localhost'
    id: int
    base_port: int = 6000 # all replicas have the same base port, to ease the connection process
    port: int
    primary_copy_id: int
    value: int
    local_changes: int
    main_sockets: dict = {} # saves main connections with other replicas, for main communication
    hat_sockets: dict = {} # saves auxiliary connections for hat_exchange communication (to ease ordering and avoid conflicts)
    history = []
    listener_socket: sock.socket #starter socket, to listen and start all the connections
    requesting_hat_count: int = 0

    condition = threading.Condition()
    lock = threading.Lock()
    update_thread: threading.Thread = None


    def __init__(self, id):
        self.id = id
        self.port = self.base_port + id
        self.primary_copy_id = 1 # replica 1 starts holding the primary copy
        self.value = 0
        self.local_changes = 0
        self.listener_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)

        self._init_listener()

    def _init_listener(self):
        self.listener_socket.bind((self.ip, self.port))
        self.listener_socket.listen(5)


    def accept_connection(self, socket_list):
        (client_socket, address) = self.listener_socket.accept()

        message = client_socket.recv(MAX_MESSAGE_SIZE_RECV)

        # since we're doing a program without fault tolerance, in case a replica crashes or noticeably fail
        # all replicas will disconnect and the program will stop
        # in a real situation, there would be some kind of technique used to handle this and replace
        # (in case the primary copy fails)

        if not message:
            print('Other replica disconnected. Closing program...')
            self.disconnect_all()

        id = _unpack_id(message)
        socket_list[id] = client_socket
        return client_socket


    def connect(self, id, socket_list):
        new_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        new_socket.connect((self.ip, self.base_port + id))

        # send your id when connecting, so the other replica know which one you are
        id_message = _pack_id(self.id)
        new_socket.sendall(id_message) 
        socket_list[id] = new_socket

        return new_socket


    def _request_write(self, id):
        with self.condition:
            self.requesting_hat_count += 1
            while self.local_changes > 0:
                self.condition.wait() # if there are still changes to commit, wait until commit notifies it's done
            
            # when there are no more uncommited local changes:
            if self.primary_copy_id == self.id: # if you are the current primary copy, give the hat to the first replica that requested
                success_message = _pack_status(int(Status.OK.value))
                self.hat_sockets[id].sendall(success_message)
                self.primary_copy_id = id

            else: # if you already gave the hat, send an error message to any other replica that requested
                fail_message = _pack_status(int(Status.ERROR.value))
                self.hat_sockets[id].sendall(fail_message)

            self.requesting_hat_count -= 1            
            self.condition.notifyAll() # notify commit that there was a change in the number of pending requests



    def receive(self, client_socket):
        self.lock.acquire() # lock in order to avoid race condition with primary copy request
        message = client_socket.recv(MAX_MESSAGE_SIZE_RECV)

        if not message:
            print('Other replica disconnected. Closing program...')
            self.disconnect_all()

        method = _unpack_method(message)

        if method == Method.UPDATE_VALUE.value:
            id, value = _unpack_update_value(message[3:])
            self._update_value(id, value)

        elif method == Method.ANNOUNCE_PRIMARY.value:
            id = _unpack_id(message[3:])
            self.update_primary_copy(id)

        elif method == Method.REQUEST_WRITE.value:
            id = _unpack_id(message[3:])
            # starts a thread to handle a replica requesting the hat
            thread = threading.Thread(target=self._request_write, args=(id,))
            thread.start()

        self.lock.release()


    def commit(self):
        if (self.local_changes == 0):
            return 'No local changes to commit'
        else:
            changes = self.local_changes

            update_message = _pack_update_value(self.id, self.value)
            self._multicast(update_message) # sends the last updated value to all replicas

            # will notify waiting thread handling primary copy request when all local changes are commited
            with self.condition: 
                self.local_changes = 0
                self.condition.notify() # notify write request thread that there was a change in local changes

                while self.requesting_hat_count > 0:
                    self.condition.wait() # wait until there are no longer any pending write requests

                
            return str(changes) + ' changes successfully commited'


    def update_primary_copy(self, primary_copy_id):
        self.primary_copy_id = primary_copy_id

    
    def _request_primary_copy(self, value):
        request_primary = _pack_request_write(self.id)
        primary_socket = self.main_sockets[self.primary_copy_id]

        primary_socket.sendall(request_primary) # send request using main socket

        # but wait for answer in auxiliary socket, to let the replica listen for commits in the value
        # even before receiving the hat

        message = self.hat_sockets[self.primary_copy_id].recv(MAX_MESSAGE_SIZE_RECV)
        if not message:
            print('Other replica disconnected. Closing program...')
            self.disconnect_all()

        status = _unpack_status(message)

        with self.lock: # to avoid race with receive
            if status == Status.OK.value: # when it receives the hat, notify everyone of change in primary copy
                self.update_primary_copy(self.id)
                self._notify_primary_copy()

                self.local_changes += 1
                self._update_value(self.id, value)
                print('Value updated')
            
            else: # in case you asked a replica that is no longer the primary
                # also applies when you were not the first to request hat from primary replica
                print('You can not alter the value')


    def change_value(self, new_value):
        if self.primary_copy_id == self.id:
            self.local_changes += 1
            self._update_value(self.id, new_value)
            return True, 'Value updated'

        else: # ask for the primary copy
            if self.update_thread is not None and self.update_thread.is_alive():
                # when there is already a thread handling the request and waiting for an answer
                return False, 'Waiting for primary copy'
            
            else: # start a thread to handle sending and receiving the hat (or a denial message)
                self.update_thread = threading.Thread(target=self._request_primary_copy, args=(new_value,))
                self.update_thread.start()

                return False, 'Requesting primary copy'


    def _update_value(self, origin_replica, new_value):
        self.value = new_value
        self.history.append((origin_replica, new_value))


    def _notify_primary_copy(self):
        announce_message = _pack_announce_primary(self.id)
        self._multicast(announce_message)


    def _multicast(self, message):
        for id, socket in self.main_sockets.items():
            socket.sendall(message)


    def contains(self, socket):
        id = self._get_id_by_socket(socket)
        if id:
            return True
        else:
            return False


    def _get_id_by_socket(self, socket):
        found_id = None
        for id, client_socket in self.main_sockets.items():
            if client_socket == socket:
                found_id = id

        return found_id


    def disconnect_all(self):
        for id, client_socket in self.main_sockets.items():
            client_socket.close()

        for id, hat_socket in self.hat_sockets.items():
            hat_socket.close()
        
        self.listener_socket.close()
        sys.exit()


def print_instructions():
    print('To read the value, enter \'/read\'')
    print('To get primary copy replica id, enter \'/primary\'')
    print('To get local history, enter \'/history\'')
    print('To alter the value, enter \'/update new_value\'')
    print('To commit all alterations, enter \'/commit\'')
    print('To close the program, enter \'/close\'')


def main(id: int):
    inputs = [sys.stdin]
    replica = Replica(id)

    print('Getting ready...')
    # connects all the main sockets
    for i in range(2, replica.id + 1):
        inputs.append(replica.accept_connection(replica.main_sockets))
    
    for i in range(replica.id + 1, 5):
        while True:
            try:
                inputs.append(replica.connect(i, replica.main_sockets))
                break

            except ConnectionRefusedError:
                pass


    # connects all the auxiliary hat sockets
    for i in range(2, replica.id + 1):
        replica.accept_connection(replica.hat_sockets)
    
    for i in range(replica.id + 1, 5):
        while True:
            try:
                replica.connect(i, replica.hat_sockets)
                break

            except ConnectionRefusedError:
                pass


    print('Ready!')
    print_instructions()

    while True:
        r, w, err = select.select(inputs, [], [])

        for read in r:
            if replica.contains(read): # reads main sockets
                replica.receive(read)

            elif read == sys.stdin:
                command = input()
                request = command.split(' ')
                head = request[0]

                if head == '/read':
                    print(replica.value)

                elif head == '/primary':
                    print(replica.primary_copy_id)

                elif head == '/history':
                    history = replica.history
                    if not history:
                        print('There were no alterations in the value so far')
                    else:
                        print(history)

                elif head == '/update' and len(request) > 1:
                    value = request[1]
                    try:
                        value = int(value)
                        status, message = replica.change_value(value)
                        print(message)

                    except ValueError:
                        print('The value needs to be an integer')

                elif head == '/commit':
                    message = replica.commit()
                    print(message)

                elif head == '/close':
                    replica.disconnect_all()

                else:
                    print('Command not found')


if __name__ == "__main__":
    main(int(sys.argv[1]))