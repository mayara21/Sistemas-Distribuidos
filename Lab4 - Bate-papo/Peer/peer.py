import json
import multiprocessing
import threading
import socket as sock
import select
import sys
import struct
from user import User
from request import Request
from status import Status

SERVER_HOST: str = '127.0.0.1'
SERVER_PORT: int = 9000

LISTENER_SOCKET_HOST: str = '127.0.0.1'
LISTENER_SOCKET_PORT: int = 6000

SEND_ID = 'ID'

inputs = [sys.stdin]

ENCODING: str = 'utf-8'

my_name = ''

connections: dict = {}


def unpack_user_message(msg: bytearray):
    user_ip: str = ''

    for i in range(16, 19):
        user_ip += str(struct.unpack('=B', msg[i:i + 1])[0]) + '.'
    
    user_ip += str(struct.unpack('=B', msg[19:20])[0])

    user_name = str(struct.unpack('=16s', msg[:16])[0], encoding=ENCODING)
    user_name = user_name.strip('\x00')

    user_port = int((struct.unpack('=H', msg[20:22])[0]))

    new_user: User = User(user_name, user_ip, user_port)

    return new_user


def unpack_get_list_response(msg: bytearray):
    list_size = int(struct.unpack('=H', msg[:2])[0])
    user_list = []

    for i in range(list_size):
        j = 2 + i*16
        user = str(struct.unpack('=16s', msg[j: j + 16])[0], encoding=ENCODING).strip('\x00')
        user_list.append(user)

    return user_list


def structure_connect_chat_request(name: str):
    method: str = Request.ENTER_CHAT.value
    bytes_method: bytes = struct.pack('=8s', method.encode(ENCODING))
    bytes_name: bytes = struct.pack('=16s', name.encode(ENCODING))

    bytes_ip: bytes = b''
    ip_parts: list = LISTENER_SOCKET_HOST.split(".")
    for part in ip_parts:
        bytes_ip += struct.pack('=B', int(part))
    
    bytes_port: bytes = struct.pack('=H', LISTENER_SOCKET_PORT)

    return (bytes_method + bytes_name + bytes_ip + bytes_port)


def structure_get_user_request(name: str):
    method: str = Request.GET_USER.value
    bytes_method: bytes = struct.pack('=8s', method.encode(ENCODING))
    bytes_name: bytes = struct.pack('=16s', name.encode(ENCODING))

    return bytes_method + bytes_name


def structure_check_user_request(name: str):
    method: str = Request.CHECK_USER_CONNECTION.value
    bytes_method: bytes = struct.pack('=8s', method.encode(ENCODING))
    bytes_name: bytes = struct.pack('=16s', name.encode(ENCODING))

    return bytes_method + bytes_name


def structure_get_list_request():
    method: str = Request.LIST_USERS.value
    bytes_method: bytes = struct.pack('=8s', method.encode(ENCODING))

    return bytes_method


def unpack_message(message):
    name = str(struct.unpack('=16s', message[:16])[0], encoding=ENCODING).strip('\x00')
    message_size = int(struct.unpack('=H', message[16:18])[0])

    message = str(struct.unpack('=' + str(message_size) + 's', message[18:])[0], encoding=ENCODING)

    return (name, message)


def pack_message(message):
    name_bytes: bytes = struct.pack('=16s', my_name.encode(ENCODING))
    message_size = len(message)
    message_size_bytes: bytes = struct.pack('=H', message_size)

    message_bytes = struct.pack('=' + str(message_size) + 's', message.encode(ENCODING))

    return name_bytes + message_size_bytes + message_bytes


def init_listener():
    socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    socket.bind((LISTENER_SOCKET_HOST, LISTENER_SOCKET_PORT))

    socket.listen(5)
    socket.setblocking(False)

    inputs.append(socket)

    return socket


def unpack_get_user_on_connect(message):
    name = str(struct.unpack('=16s', message[:16])[0], encoding=ENCODING).strip('\x00')
    return name


def pack_get_user_on_connect():
    bytes_method: bytes = struct.pack('=8s', SEND_ID.encode(ENCODING))
    bytes_name: bytes = struct.pack('=16s', my_name.encode(ENCODING))
    return bytes_method + bytes_name


def accept_conection(socket):
    (client_socket, address) = socket.accept()
    print(client_socket, address)

    msg = client_socket.recv(4096)

    user_name = unpack_get_user_on_connect(msg[8:])

    connections[user_name] = client_socket

    return (client_socket, address)


def receive(client_sock, shutdown_event: threading.Event):
    client_sock.setblocking(False)
    while True:
        ready = select.select([client_sock], [], [], 1)[0]

        if ready:
            message = client_sock.recv(4096)

            if not message:
                print('fechou')
                client_sock.close()
                return

            (user, msg) = unpack_message(message)

            print('(' + user + '): ' + msg)

        else:
            if shutdown_event.is_set():
                client_sock.close()
                return


def connect(socket, user_ip, user_port, shutdown_event: threading.Event):
    print('Conectando a ' + user_ip + ' ' + str(user_port))

    socket.connect((user_ip, user_port))
    id_msg = pack_get_user_on_connect()
    print(id_msg)
    send(socket, id_msg)

    receive(socket, shutdown_event)


def send(socket, msg):
    print('Sending message')
    socket.sendall(msg)
    print('enviei')
        


def main():
    socket = sock.socket()
    socket.connect((SERVER_HOST, SERVER_PORT))

    shutdown_event = threading.Event()

    while True:
        name: str = input('Enter the name you want to use in the chat: ')

        if (name.lower() == 'close'): 
            break
            
        connect_chat_request = structure_connect_chat_request(name)
        socket.sendall(connect_chat_request)

        connection_response = socket.recv(4096)
            
        status = int(struct.unpack('=B', connection_response[8:9])[0])

        if status == Status.OK.value:
            global my_name 
            my_name = name.lower()
            break
        else:
            error_message = str(struct.unpack('=256s', connection_response[9:265])[0], encoding=ENCODING).strip('\x00')
            print(error_message)


    clients = [] 
    listener_socket = init_listener()
    print('Ready to listen...\nType close to terminate execution')

    while True:
        r, w, err = select.select(inputs, [], [])

        for read in r:
            if read == listener_socket:
                client_sock, address = accept_conection(listener_socket)
                print('Connected with: ', address)

                client = threading.Thread(target=receive, args=[client_sock, shutdown_event])
                client.start()

                clients.append(client)

            elif read == sys.stdin: 
                cmd = input()
                if cmd == 'close':
                    shutdown_event.set()
                    for c in clients: 
                        c.join()

                    socket.close() 
                    sys.exit()

                request = cmd.split(' ')

                if request[0].lower() == '/list':
                    get_list_request = structure_get_list_request()
                    socket.sendall(get_list_request)

                    get_list_response = socket.recv(4096)

                    user_list = unpack_get_list_response(get_list_response[9:])
                    print (user_list)


                elif request[0].lower() == '/connect':
                    name = request[1]

                    get_user_request = structure_get_user_request(name)
                    socket.sendall(get_user_request)
                    get_user_response = socket.recv(4096)
                    status = int(struct.unpack('=B', get_user_response[8:9])[0])

                    if status == Status.OK.value:
                        user = unpack_user_message(get_user_response[9:])
                        print(str(user.ip_address) + ', ' + str(user.port) + ', ' + user.name)

                        new_socket = sock.socket()
                        connections[user.name] = new_socket
                        print(connections[user.name])

                        client = threading.Thread(target=connect, args=(new_socket, user.ip_address, user.port, shutdown_event))
                        client.start()
                        clients.append(client)

                    else:
                        error_message = str(struct.unpack('=256s', get_user_response[9:265])[0], encoding=ENCODING).strip('\x00')
                        print(error_message)

                
                elif request[0].lower() == '/check':
                    user_name = request[1]
                    check_user_request = structure_check_user_request(user_name)

                    socket.sendall(check_user_request)


                elif request[0] == '/send':
                    name = request[1]
                    message = ' '.join(request[2:])

                    msg = pack_message(message)
                    send(connections[name], msg)

                elif request[0] == '/disconnect':
                    name = request[1]
                    socket = connections.pop(name)
                    print('fechando socket ', socket)
                    socket.close()
                
            

if __name__ == "__main__":
    main()