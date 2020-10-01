import json
import socket as sock
import select
import sys
import struct
from user import User
from request import Request

SERVER_HOST: str = '127.0.0.1'
SERVER_PORT: int = 6000

LISTENER_SOCKET_HOST: str = '127.0.0.1'
LISTENER_SOCKET_PORT: int = 7000

ENCODING: str = 'utf-8'


def structure_user_message(name: str):
    method: str = Request.ENTER_CHAT.value
    bytes_method: bytes = struct.pack('=8s', method.encode(ENCODING))
    bytes_name: bytes = struct.pack('=16s', name.encode(ENCODING))

    bytes_ip: bytes = b''
    ip_parts: list = LISTENER_SOCKET_HOST.split(".")
    for part in ip_parts:
        bytes_ip += struct.pack('=B', int(part))
    
    bytes_port: bytes = struct.pack('=H', LISTENER_SOCKET_PORT)

    return (bytes_method + bytes_name + bytes_ip + bytes_port)


def main():
    socket = sock.socket()
    socket.connect((SERVER_HOST, SERVER_PORT))


    while True:
        name: str = input('Enter the name you want to use in the chat: ')

        if (name.lower() == 'close'): 
            break

        
        connect_chat_request = structure_user_message(name)
        
        socket.sendall(connect_chat_request)

        received_message = socket.recv(4096)

        status = str(received_message, encoding=ENCODING)

        if (status == "OK"): break

        print(status)


    while True:
        request: str = input("What? ")

        if (request.lower() == 'close'): 
            break
        
        print(request)
        if (request == 'list'):
            socket.sendall(b'list')

            user_list = socket.recv(4096)

            print(str(user_list, encoding=ENCODING))

    socket.close()

if __name__ == "__main__":
    main()