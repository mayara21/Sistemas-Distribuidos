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
user_list = [User('ana', '', 0)]


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

def send_error_response(client_sock, request_type, error_message):
    method_bytes: bytes = struct.pack('=8s', request_type.encode(ENCODING))
    status_bytes: bytes = struct.pack('=B', Status.ERROR.value)
    error_message: bytes = struct.pack('=256s', error_message.encode(ENCODING))

    error_response: bytes = method_bytes + status_bytes + error_message
    print(error_response)

    client_sock.sendall(error_response)

def send_ok_response(client_sock, request_type):
    method_bytes: bytes = struct.pack('=8s', request_type.encode(ENCODING))
    status_bytes: bytes = struct.pack('=B', Status.OK.value)

    ok_response: bytes = method_bytes + status_bytes

    client_sock.sendall(ok_response)


def handle_connection_request(client_sock, user):
    for member in user_list:
        if member.name == user.name:
            error_message = 'Name ' + user.name + ' already in use, choose another'
            send_error_response(client_sock, Request.ENTER_CHAT.value, error_message)
            return 
    
    user_list.append(user)
    send_ok_response(client_sock, Request.ENTER_CHAT.value)
    print(user_list)


def serve(client_sock, address):
    while True:
        request = client_sock.recv(4096)

        if not request:
            print('> Client ' + str(address) + ' disconnected') 
            client_sock.close()
            return

        method = str(struct.unpack('=8s', request[:8])[0], encoding=ENCODING).strip('\x00')

        if (method == Request.ENTER_CHAT.value):
            user: User = unpack_user_message(request[8:])
            handle_connection_request(client_sock, user)


        if request == 'list':
            data = json.dumps(user_list, ensure_ascii=False)
            client_sock.sendall(data.encode())
                
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