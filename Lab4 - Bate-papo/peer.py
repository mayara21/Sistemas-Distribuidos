import json
import socket as sock
import select
import sys
import struct
from user import User
from request import Request
from status import Status

SERVER_HOST: str = '127.0.0.1'
SERVER_PORT: int = 7000

LISTENER_SOCKET_HOST: str = '127.0.0.1'
LISTENER_SOCKET_PORT: int = 7000

ENCODING: str = 'utf-8'


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


def finish(socket):
    socket.close()


def main():
    socket = sock.socket()
    socket.connect((SERVER_HOST, SERVER_PORT))

    while True:
        name: str = input('Enter the name you want to use in the chat: ')

        if (name.lower() == 'close'): 
            finish(socket)
            
        connect_chat_request = structure_connect_chat_request(name)
        socket.sendall(connect_chat_request)

        connection_response = socket.recv(4096)
            
        status = int(struct.unpack('=B', connection_response[8:9])[0])

        if status == Status.OK.value:
            break
        else:
            error_message = str(struct.unpack('=256s', connection_response[9:265])[0], encoding=ENCODING).strip('\x00')
            print(error_message)

    while True:
        request: str = input("What? ")

        if (request.lower() == 'close'): 
            break
                
        fragmented_request = request.split(' ')
        print(fragmented_request)

        if fragmented_request[0].lower() == '/connect':
            user_name = fragmented_request[1]
            get_user_request = structure_get_user_request(user_name)

            socket.sendall(get_user_request)
            get_user_response = socket.recv(4096)

            status = int(struct.unpack('=B', get_user_response[8:9])[0])

            if status == Status.OK.value:
                user = unpack_user_message(get_user_response[9:])
                print(user)

            else:
                error_message = str(struct.unpack('=256s', get_user_response[9:265])[0], encoding=ENCODING).strip('\x00')
                print(error_message)

        elif fragmented_request[0].lower() == '/check':
            print('checa ai pfv')
            user_name = fragmented_request[1]
            check_user_request = structure_check_user_request(user_name)

            socket.sendall(check_user_request)

        elif fragmented_request[0].lower() == '/list':
            print('lista ai por favor')
            get_list_request = structure_get_list_request()
            socket.sendall(get_list_request)

            get_list_response = socket.recv(4096)

            user_list = unpack_get_list_response(get_list_response[9:])
            print (user_list)


if __name__ == "__main__":
    main()