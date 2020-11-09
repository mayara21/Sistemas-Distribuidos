import socket as sock
import sys
import select
import threading
from enum import Enum
import struct

ENCODING = 'utf-8'
MAX_MESSAGE_SIZE_RECV = 4096

class Method(Enum):
    NEW_CONNECTION = 'CON'
    UPDATE_VALUE = 'NEW'
    ANNOUNCE_PRIMARY = 'PRI'
    REQUEST_WRITE = 'WRI'


class Status(Enum):
    OK = 0
    ERROR = 1


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
    base_port: int = 6000
    port: int
    primary_copy_id: int
    value: int
    local_changes: int
    connections: dict = {}
    history = []
    listener_socket: sock.socket
    requesting_hat_count: int = 0

    condition = threading.Condition()

    def __init__(self, id):
        self.id = id
        self.port = self.base_port + id
        self.primary_copy_id = 1
        self.value = 0
        self.local_changes = 0
        self.listener_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)

        self._init_listener()

    def _init_listener(self):
        self.listener_socket.bind((self.ip, self.port))
        self.listener_socket.listen(5)


    def accept_connection(self, inputs):
        (client_socket, address) = self.listener_socket.accept()
        inputs.append(client_socket)

        message = client_socket.recv(MAX_MESSAGE_SIZE_RECV)

        id = _unpack_id(message)
        self.connections[id] = client_socket
        return (client_socket, address, id)


    def connect(self, id, inputs):
        new_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)     
        new_socket.connect((self.ip, self.base_port + id))
        id_message = _pack_id(self.id)
        new_socket.sendall(id_message)
        self.connections[id] = new_socket
        inputs.append(new_socket)

        return new_socket


    def _request_write(self, client_socket, id):
        with self.condition:
            self.requesting_hat_count += 1
            while self.local_changes > 0:
                self.condition.wait()
            
            if self.primary_copy_id == self.id:
                success_message = _pack_status(int(Status.OK.value))
                client_socket.sendall(success_message)
                self.primary_copy_id = id

            else:
                fail_message = _pack_status(int(Status.ERROR.value)) # add error message
                client_socket.sendall(fail_message)

            self.requesting_hat_count -= 1            
            self.condition.notifyAll()



    def receive(self, client_socket):
        message = client_socket.recv(MAX_MESSAGE_SIZE_RECV)
        print('Received a message', message)
        method = _unpack_method(message)

        if method == Method.UPDATE_VALUE.value:
            id, value = _unpack_update_value(message[3:])
            print('Received new value')
            self._update_value(id, value)

        elif method == Method.ANNOUNCE_PRIMARY.value:
            id = _unpack_id(message[3:])
            self.update_primary_copy(id)

        elif method == Method.REQUEST_WRITE.value:
            id = _unpack_id(message[3:])
            thread = threading.Thread(target=self._request_write, args=(client_socket, id))
            thread.start()


    def commit(self):
        if (self.local_changes == 0):
            return 'No local changes to commit'
        else:
            changes = self.local_changes

            with self.condition:
                self.local_changes = 0
                self.condition.notify()

                while self.requesting_hat_count > 0:
                    self.condition.wait()

            update_message = _pack_update_value(self.id, self.value)
            self._multicast(update_message)
                
            return str(changes) + ' changes successfully commited'


    def update_primary_copy(self, primary_copy_id):
        self.primary_copy_id = primary_copy_id


    def change_value(self, new_value):
        if self.primary_copy_id == self.id:
            self.local_changes += 1
            self._update_value(self.id, new_value)
            return True, 'Value updated'

        else: # ask for the primary copy
            request_primary = _pack_request_write(self.id)
            primary_socket = self.connections[self.primary_copy_id]

            primary_socket.sendall(request_primary)
            print('enviei')
            message = primary_socket.recv(MAX_MESSAGE_SIZE_RECV)
            print('return: ', message)
            status = _unpack_status(message)

            if status == Status.OK.value:
                self.update_primary_copy(self.id)
                self._notify_primary_copy()

                self.local_changes += 1
                self._update_value(self.id, new_value)
                return True, 'Value updated'
            
            else:
                return False, 'You can not alter the value'


    def _update_value(self, origin_replica, new_value):
        self.value = new_value
        self.history.append((origin_replica, new_value))


    def _notify_primary_copy(self):
        announce_message = _pack_announce_primary(self.id)
        self._multicast(announce_message)


    def _multicast(self, message):
        for id, socket in self.connections.items():
            socket.sendall(message)


    def contains(self, socket):
        id = self._get_id_by_socket(socket)
        if id:
            return True
        else:
            return False


    def _get_id_by_socket(self, socket):
        found_id = None
        for id, client_socket in self.connections.items():
            if client_socket == socket:
                found_id = id

        return found_id

    def disconnect_all(self):
        for id, client_socket in self.connections.items():
            client_socket.close()
        
        self.listener_socket.close()


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
    for i in range(2, replica.id + 1):
        replica.accept_connection(inputs)
    
    for i in range(replica.id + 1, 5):
        while True:
            try:
                replica.connect(i, inputs)
                break

            except ConnectionRefusedError:
                pass

    print('Ready!')
    print_instructions()

    while True:
        r, w, err = select.select(inputs, [], [])

        for read in r:
            if replica.contains(read):
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
                    sys.exit()

                else:
                    print('Command not found')

            else:
                print('Outro')


if __name__ == "__main__":
    main(int(sys.argv[1]))