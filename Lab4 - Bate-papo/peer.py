import json
import socket as sock
import select
from user import User
from request import Request

SERVER_HOST: str = 'localhost'
SERVER_PORT: int = 6000

LISTENER_SOCKET_HOST: str = 'localhost'
LISTENER_SOCKET_PORT: int = 7000


def main():
    socket = sock.socket()
    socket.connect((SERVER_HOST, SERVER_PORT))


    while True:
        name: str = input('Enter the name you want to use in the chat: ')

        if (name.lower() == 'close'): 
            break

        socket.sendall(name.encode('utf-8'))

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