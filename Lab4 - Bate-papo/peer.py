import json
import socket as sock
import select
import sys
import struct
from user import User
from request import Request

SERVER_HOST: str = '127.0.0.1'
SERVER_PORT: int = 7000

LISTENER_SOCKET_HOST: str = '127.0.0.1'
LISTENER_SOCKET_PORT: int = 7000


def structure_user_message(name: str):
    bytes_name = struct.pack('=16s', name.encode('utf-8'))

    bytes_ip = b''
    ip_parts = LISTENER_SOCKET_HOST.split(".")
    for part in ip_parts:
        bytes_ip += struct.pack('=B', int(part))
    
    bytes_port = struct.pack('=H', LISTENER_SOCKET_PORT)

    return (bytes_name + bytes_ip + bytes_port)


def main():
    socket = sock.socket()
    socket.connect((SERVER_HOST, SERVER_PORT))


    while True:
        name: str = input('Enter the name you want to use in the chat: ')

        if (name.lower() == 'close'): 
            break

        
        user = structure_user_message(name)
        
        socket.sendall(user)

        received_message = socket.recv(4096)

        status = str(received_message, encoding='utf-8')

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

            print(str(user_list, encoding='utf-8'))

    socket.close()

if __name__ == "__main__":
    main()