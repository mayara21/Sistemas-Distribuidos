import threading
import select
import socket as sock
import sys
from user import User
from method import Method
from status import Status
from message_mapper import Message_Mapper

HOST: str = ''
PORT: int = 9000

MAX_MESSAGE_SIZE_RECV = 4096

inputs = [sys.stdin]
user_list = []
connections: dict = {}

def init_server():
    socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    socket.bind((HOST, PORT))

    socket.listen(5)
    socket.setblocking(False)

    inputs.append(socket)

    return socket


def accept_conection(socket):
    return socket.accept()


def send_error_response(client_sock, request_type, error_message):
    error_response = Message_Mapper.pack_error_response(request_type, error_message)
    client_sock.sendall(error_response)


def send_ok_response(client_sock, request_type):
    ok_response = Message_Mapper.pack_ok_response(request_type)
    client_sock.sendall(ok_response)


def send_get_user_response(client_sock, user, request_type):
    user_response = Message_Mapper.pack_get_user_response(user.name, user.ip_address, user.port)
    client_sock.sendall(user_response)


def handle_connection_request(client_sock, user):
    for member in user_list:
        if member.name == user.name:
            error_message = 'Name ' + user.name + ' already in use, choose another'
            send_error_response(client_sock, Method.ENTER_CHAT.value, error_message)
            return 
    
    user_list.append(user)
    connections[user.name] = client_sock
    send_ok_response(client_sock, Method.ENTER_CHAT.value)


def handle_get_user_request(client_sock, name):
    for member in user_list:
        if member.name == name:
            send_get_user_response(client_sock, member, Method.GET_USER.value)
            return

    error_message = 'User ' + name + ' is not connect to the chat'
    send_error_response(client_sock, Method.GET_USER.value, error_message)


def send_list_response(client_sock, simplified_list):
    message = Message_Mapper.pack_get_list_response(simplified_list)
    client_sock.sendall(message)


def get_simplified_list():
    simplified_list = []
    for user in user_list:
        simplified_list.append(user.name)

    return simplified_list


def handle_get_list_request(client_sock):
    simplified_list = get_simplified_list()
    send_list_response(client_sock, simplified_list)


def handle_check_request(name):
    for user in user_list:
        if user.name == name:
            validate_connection(name)
            return

def handle_validate_message(client_sock, message):
    status = Message_Mapper.unpack_status(message)

    if status != Status.OK.value:
        aux = connections

        for user_name, socket in aux.items():
            if socket == client_sock:
                connections.pop(user_name)
                remove_user(user_name)          
                socket.close()

                print(user_name + ' disconnected from chat')
                return

    else:
        print('User still active')


def validate_connection(name):
    validation: bytes = Message_Mapper.pack_validate_user_message()
    socket = connections[name]
    socket.sendall(validation)


def remove_user(name: str):
    for user in user_list:
        if user.name == name:
            user_list.remove(user)


def serve(client_sock, address):
    while True:
        request = client_sock.recv(MAX_MESSAGE_SIZE_RECV)

        if not request:
            aux = connections

            for user_name, socket in aux.items():
                if socket == client_sock:
                    connections.pop(user_name)
                    remove_user(user_name)          
                    socket.close()

                    print(user_name + ' disconnected from chat')
                    return

            print(str(address) + ' disconnected before informing a name')
            client_sock.close()
            return

        method = Message_Mapper.unpack_method(request)
        message = request[8:]

        if method == Method.ENTER_CHAT.value:
            user: User = Message_Mapper.unpack_connect_request(message)
            handle_connection_request(client_sock, user)
        
        elif method == Method.GET_USER.value:
            user_name: str = Message_Mapper.unpack_get_user_request(message)
            print(user_name)
            handle_get_user_request(client_sock, user_name)

        elif method == Method.CHECK_USER_CONNECTION.value:
            user_name: str = Message_Mapper.unpack_check_user_request(message )
            handle_check_request(user_name)

        elif method == Method.LIST_USERS.value:
            handle_get_list_request(client_sock)

        elif method == Method.VALIDATE_CONNECTION.value:
            handle_validate_message(client_sock, message)
        


def main():
    clients = [] # saves the created threads to join them
    socket = init_server()
    print('Server Ready...\nType /close to terminate server execution')
    
    while True:
        r, w, err = select.select(inputs, [], [])

        for read in r:
            if read == socket:
                client_sock, address = accept_conection(socket)
                client_sock.setblocking(True)
                print('Connected with: ', address)

                client = threading.Thread(target=serve, args=(client_sock, address))
                client.start()

                clients.append(client)

            elif read == sys.stdin: 
                cmd = input()
                if cmd == '/close':
                    for c in clients: 
                        c.join()

                    socket.close() 
                    sys.exit()

                else:
                    print('Command not found.')


if __name__ == "__main__":
    main()