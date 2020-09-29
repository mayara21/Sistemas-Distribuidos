import json
import multiprocessing
import select
import socket as sock
import struct
import sys
from user import User
from request import Request

HOST: str = ''
PORT: int = 7000

ERROR_MESSAGE: str = "Name already being used."

inputs = [sys.stdin]
user_list = []


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
    user_ip = ''

    for i in range(16, 19):
        user_ip += str(struct.unpack('=B', msg[i:i + 1])[0]) + '.'
    
    user_ip += str(struct.unpack('=B', msg[19:20])[0])

    user_name = str(struct.unpack('=16s', msg[:16])[0], encoding='utf-8')
    user_port = int((struct.unpack('=H', msg[20:22])[0])) 
    print(user_name)
    print(user_port)
    print(user_ip)


def serve(client_sock, address):
    while True:
        user = client_sock.recv(4096)

        if not user:
            print('> Client ' + str(address) + ' disconnected') 
            client_sock.close()
            return

        unpack_user_message(user)

        if user == 'list':
            data = json.dumps(user_list, ensure_ascii=False)
            client_sock.sendall(data.encode())

        if user.capitalize() in user_list:
            client_sock.sendall(ERROR_MESSAGE.encode('utf-8'))
                
        client_sock.sendall(b'OK')
        


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