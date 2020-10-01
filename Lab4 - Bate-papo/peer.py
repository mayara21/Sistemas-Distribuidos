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

def finish(socket):
    socket.close()


def main():
    socket = sock.socket()
    socket.connect((SERVER_HOST, SERVER_PORT))

    while True:
        while True:
            name: str = input('Enter the name you want to use in the chat: ')

            if (name.lower() == 'close'): 
                finish(socket)
            
            connect_chat_request = structure_user_message(name)
            socket.sendall(connect_chat_request)

            connection_response = socket.recv(4096)
            
            status = int(struct.unpack('=B', connection_response[8:9])[0])

            if status == Status.OK.value:
                break
            else:
                error_message = str(struct.unpack('=256s', connection_response[9:265])[0], encoding=ENCODING).strip('\x00')
                print(error_message)

        request: str = input("What? ")

        if (request.lower() == 'close'): 
            finish(socket)
        
        print(request)
        if (request == 'list'):
            socket.sendall(b'list')

            user_list = socket.recv(4096)

            print(str(user_list, encoding=ENCODING))


if __name__ == "__main__":
    main()