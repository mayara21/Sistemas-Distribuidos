import socket as sock
import sys
import threading
from server_thread_manager import ServerThreadManager
from message_mapper import MessageMapper
from connections_lister import connections_lister
from user_lister import user_lister
from method import Method
from user import User
from status import Status

HOST: str = ''
PORT: int = 9000

MAX_MESSAGE_SIZE_RECV: int = 4096

class ServerController:

    socket: sock.socket
    thread_manager: ServerThreadManager

    def __init__(self):
        self.thread_manager = ServerThreadManager()
        self.socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        try:
            self.socket.bind((HOST, PORT))
        except OSError as error:
            print('OS error: {0}'.format(error))
            self.close_server()

        self.socket.listen(5)
        self.socket.setblocking(False)


    def accept_new_peer(self):
        try:
            client_sock, address = self.socket.accept()
            client_sock.setblocking(True)

            client = self.thread_manager.create_thread(self.serve, (client_sock, address))
            client.start()
            return (True, address)

        except OSError as error:
            return (False, 'OS error: {0}'.format(error))


    def close_server(self):
        self.thread_manager.join_threads
        self.socket.close()
        sys.exit()

    def close_connection(self, client_socket, address=''):
        name = connections_lister.pop_connection_by_socket(client_socket)[0]
        
        if not name:
            print(str(address) + ' disconnected before informing a name')
            client_socket.close() 

        else:
            user_lister.remove_from_list(name)
            client_socket.close()
            print(name + ' disconnected from chat')


    def serve(self, client_sock, address):
        while True:
            request = client_sock.recv(MAX_MESSAGE_SIZE_RECV)

            if not request:
                self.close_connection(client_sock, address)
                return

            method = MessageMapper.unpack_method(request)
            message = request[8:]

            if method == Method.ENTER_CHAT.value:
                user: User = MessageMapper.unpack_connect_request(message)
                self.handle_connection_request(client_sock, user)
            
            elif method == Method.GET_USER.value:
                user_name: str = MessageMapper.unpack_get_user_request(message)
                self.handle_get_user_request(client_sock, user_name)

            elif method == Method.CHECK_USER_CONNECTION.value:
                user_name: str = MessageMapper.unpack_check_user_request(message )
                self.handle_check_request(user_name)

            elif method == Method.LIST_USERS.value:
                self.handle_get_list_request(client_sock)

            elif method == Method.VALIDATE_CONNECTION.value:
                self.handle_validate_message(client_sock, message)


    def handle_connection_request(self, client_sock, new_user):
        user = user_lister.find_user_by_name(new_user.name)

        if not user:
            user_lister.add_to_list(new_user)
            connections_lister.add_connection(new_user.name, client_sock)
            self.send_ok_response(client_sock, Method.ENTER_CHAT.value)

        else:
            error_message = 'Sorry, the name ' + new_user.name + ' is already being used :(\nTry another one'
            self.send_error_response(client_sock, Method.ENTER_CHAT.value, error_message)


    def handle_get_user_request(self, client_sock, name):
        user = user_lister.find_user_by_name(name)

        if not user:
            error_message = 'User ' + name + ' is not connect to the chat'
            self.send_error_response(client_sock, Method.GET_USER.value, error_message)
        
        else: 
            self.send_get_user_response(client_sock, user, Method.GET_USER.value)

    def handle_get_list_request(self, client_sock):
        simplified_list = user_lister.get_name_list()
        self.send_list_response(client_sock, simplified_list)


    def handle_check_request(self, name):
        user = user_lister.find_user_by_name(name)
        if user:
            self.validate_connection(name)


    def handle_validate_message(self, client_sock, message):
        status = MessageMapper.unpack_status(message)

        if status != Status.OK.value:
            self.close_connection(client_sock)
        else:
            print('User still active')


    def validate_connection(self, name):
        validation: bytes = MessageMapper.pack_validate_user_message()
        socket = connections_lister.get_connection_by_name(name)
        if socket:
            socket.sendall(validation) #add timeout and exception handling
        

    def send_error_response(self, client_sock, request_type, error_message):
        error_response = MessageMapper.pack_error_response(request_type, error_message)
        client_sock.sendall(error_response)


    def send_ok_response(self, client_sock, request_type):
        ok_response = MessageMapper.pack_ok_response(request_type)
        client_sock.sendall(ok_response)


    def send_get_user_response(self, client_sock, user, request_type):
        user_response = MessageMapper.pack_get_user_response(user.name, user.ip_address, user.port)
        client_sock.sendall(user_response)


    def send_list_response(self, client_sock, simplified_list):
        message = MessageMapper.pack_get_list_response(simplified_list)
        client_sock.sendall(message)

