import json
import multiprocessing
import socket as sock
import select
import sys
import struct
from user import User

LISTENER_SOCKET_HOST: str = '127.0.0.1'
LISTENER_SOCKET_PORT: int = 6000

ENCODING: str = 'utf-8'

inputs = [sys.stdin]
my_name = 'bob'

user_list = [User('bob', '127.0.0.1', 6000), User('maria', '127.0.0.1', 5000), User('ana', '127.0.0.1', 7000)]

def init_listener():
    socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    socket.bind((LISTENER_SOCKET_HOST, LISTENER_SOCKET_PORT))

    socket.listen(5)
    socket.setblocking(False)

    inputs.append(socket)

    return socket

def accept_conection(listener_socket):
    return listener_socket.accept()


def get_user_info(name):
    for user in user_list:
        if(user.name == name):
            print('achei')
            return (user.ip_address, user.port)


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


def receive(client_sock, address):
    print('listening')
    while True:
        message = client_sock.recv(4096)

        if not message:
            print('fechou')
            client_sock.close()
            return

        (user, msg) = unpack_message(message)

        print('(' + user + '): ' + msg)


def connect(socket, user_ip, user_port):
    print('Conectando a ' + user_ip + ' ' + str(user_port))

    try:
        socket.connect((user_ip, user_port))
    except OSError:
        print('Erro ao conectar')


def send(socket, msg):
    print('Sending message')
    socket.sendall(msg)
        


def main():
    socket = sock.socket()

    clients = [] # saves the created processes to join them
    listener_socket = init_listener()
    print('Server Ready...\nType close to terminate server execution')
    print(inputs)

    while True:
        r, w, err = select.select(inputs, [], [])

        for read in r:
            if read == listener_socket:
                print('oi')
                client_sock, address = accept_conection(listener_socket)
                print('Connected with: ', address)

                client = multiprocessing.Process(target=receive, args=(client_sock, address))
                client.start()

                clients.append(client)

            elif read == sys.stdin: 
                cmd = input()
                if cmd == 'close':
                    for c in clients: 
                        c.join()

                    socket.close() 
                    sys.exit()

                request = cmd.split(' ')

                if request[0] == '/connect':
                    name = request[1]
                    user_info = get_user_info(name)
                    ip = user_info[0]
                    port = user_info[1]

                    print(str(ip) + ', ' + str(port) + ', ' + name)
                    connect(socket, ip, port)

                elif request[0] == '/send':
                    name = request[1]
                    message = request[2]
                    print(name + ': ' + message)

                    msg = pack_message(message)
                    send(socket, msg)


if __name__ == "__main__":
    main()