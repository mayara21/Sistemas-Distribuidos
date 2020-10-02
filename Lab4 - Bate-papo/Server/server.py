import json
import multiprocessing
import select
import socket as sock
import struct
import sys
from user import User
from request import Request
from status import Status

HOST: str = ''
PORT: int = 7000

ENCODING: str = 'utf-8'

inputs = [sys.stdin]
user_list = [User('ana', '127.0.0.1', 0), User('bob', '127.0.0.1', 0), User('sofia', '127.0.0.1', 0)]


def init_server():
    socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    socket.bind((HOST, PORT))

    socket.listen(5)
    socket.setblocking(False)

    inputs.append(socket)

    return socket


def accept_conection(socket):
    return socket.accept()


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


def unpack_get_user_request(msg: bytearray):
    user_name = str(struct.unpack('=16s', msg[:16])[0], encoding=ENCODING)
    user_name = user_name.strip('\x00')

    return user_name

def unpack_check_user_request(msg: bytearray):
    user_name = str(struct.unpack('=16s', msg[:16])[0], encoding=ENCODING)
    user_name = user_name.strip('\x00')

    return user_name


def send_error_response(client_sock, request_type, error_message):
    method_bytes: bytes = struct.pack('=8s', request_type.encode(ENCODING))
    status_bytes: bytes = struct.pack('=B', Status.ERROR.value)
    error_message: bytes = struct.pack('=256s', error_message.encode(ENCODING))

    error_response: bytes = method_bytes + status_bytes + error_message

    client_sock.sendall(error_response)


def send_ok_response(client_sock, request_type):
    method_bytes: bytes = struct.pack('=8s', request_type.encode(ENCODING))
    status_bytes: bytes = struct.pack('=B', Status.OK.value)

    ok_response: bytes = method_bytes + status_bytes

    client_sock.sendall(ok_response)


def send_user_response(client_sock, user, request_type):
    method_bytes: bytes = struct.pack('=8s', request_type.encode(ENCODING))
    status_bytes: bytes = struct.pack('=B', Status.OK.value)

    bytes_name: bytes = struct.pack('=16s', user.name.encode(ENCODING))

    bytes_ip: bytes = b''
    ip_parts: list = user.ip_address.split(".")
    for part in ip_parts:
        bytes_ip += struct.pack('=B', int(part))
    
    bytes_port: bytes = struct.pack('=H', user.port)

    user_response = method_bytes + status_bytes + bytes_name + bytes_ip + bytes_port

    client_sock.sendall(user_response)


def handle_connection_request(client_sock, user):
    for member in user_list:
        if member.name == user.name:
            error_message = 'Name ' + user.name + ' already in use, choose another'
            send_error_response(client_sock, Request.ENTER_CHAT.value, error_message)
            return 
    
    user_list.append(user)
    send_ok_response(client_sock, Request.ENTER_CHAT.value)


def handle_get_user_request(client_sock, name):
    for member in user_list:
        if member.name == name:
            send_user_response(client_sock, member, Request.GET_USER.value)
            return

    error_message = 'User ' + name + ' is not connect to the chat'
    send_error_response(client_sock, Request.GET_USER.value, error_message)


def send_list_response(client_sock, request_type, simplified_list):
    list_size = len(simplified_list)
    method_bytes: bytes = struct.pack('=8s', request_type.encode(ENCODING))
    status_bytes: bytes = struct.pack('=B', Status.OK.value)

    list_size_bytes: bytes = struct.pack('=H', list_size)
    names_bytes: bytes = b''

    for i in range(list_size):
        names_bytes += struct.pack('=16s', simplified_list[i].encode(ENCODING))

    list_response = method_bytes + status_bytes + list_size_bytes + names_bytes

    client_sock.sendall(list_response)


def get_simplified_list():
    simplified_list = []
    for user in user_list:
        simplified_list.append(user.name)

    return simplified_list


def handle_get_list_request(client_sock):
    simplified_list = get_simplified_list()
    send_list_response(client_sock, Request.LIST_USERS.value, simplified_list)

def validate_connection(name):
    print('Validar a conexao')


def serve(client_sock, address):
    while True:
        request = client_sock.recv(4096)

        if not request:
            client_sock.close()
            return

        method = str(struct.unpack('=8s', request[:8])[0], encoding=ENCODING).strip('\x00')

        if method == Request.ENTER_CHAT.value:
            user: User = unpack_user_message(request[8:])
            handle_connection_request(client_sock, user)
        
        elif method == Request.GET_USER.value:
            user_name: str = unpack_get_user_request(request[8:])
            handle_get_user_request(client_sock, user_name)

        elif method == Request.CHECK_USER_CONNECTION.value:
            user_name: str = unpack_check_user_request(request[8:])
            validate_connection(user_name)

        elif method == Request.LIST_USERS.value:
            handle_get_list_request(client_sock)
        


def main():
    clients = [] # saves the created processes to join them
    socket = init_server()
    print('Server Ready...\nType close to terminate server execution')
    
    while True:
        r, w, err = select.select(inputs, [], [])

        for read in r:
            if read == socket:
                client_sock, address = accept_conection(socket)
                print('Connected with: ', address)

                client = multiprocessing.Process(target=serve, args=(client_sock, address))
                client.start()

                clients.append(client)

            elif read == sys.stdin: 
                cmd = input()
                if cmd == 'close':
                    for c in clients: 
                        c.join()

                    socket.close() 
                    sys.exit()


if __name__ == "__main__":
    main()