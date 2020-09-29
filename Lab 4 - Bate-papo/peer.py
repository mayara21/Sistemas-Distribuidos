import json
import socket as sock
import select
from user import User

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

        print(str(received_message, encoding='utf-8'))

        #try:
        #    res = json.loads(str(received_message, encoding='utf-8'))
        #    print(res)

        #except json.decoder.JSONDecodeError:
        #    print(str(received_message, encoding='utf8'))


    socket.close()

if __name__ == "__main__":
    main()