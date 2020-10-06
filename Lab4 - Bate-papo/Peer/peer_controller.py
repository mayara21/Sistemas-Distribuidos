import socket as sock
import sys
import errno
from user import User
from method import Method
from message_mapper import MessageMapper
from status import Status
from peer_connections_lister import connections_lister
from peers_lister import peers_lister

SERVER_HOST: str = '127.0.0.1'
SERVER_PORT: int = 9000

LISTENER_SOCKET_HOST: str = '127.0.0.1'

MAX_MESSAGE_SIZE_RECV = 4096

class PeerController:

    socket: sock.socket
    listener_socket: sock.socket

    def __init__(self):
        self.socket = sock.socket()
        self.listener_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)

    def connect_server(self):
        try:
            self.socket.connect((SERVER_HOST, SERVER_PORT))
            return (True, '')

        except OSError as error:
            error_message = self.handle_error_server(error.errno)
            return (False, error_message)


    def init_listener_socket(self):
        try:
            self.listener_socket.bind((LISTENER_SOCKET_HOST, 0))

        except OSError as error:
            error_message = 'OS error: {0}'.format(error)
            return (False, error_message)

        self.listener_socket.listen(5)
        self.listener_socket.setblocking(False)

        return (True, '')

    def disconnect_from_chat(self):
        connections = connections_lister.get_all_connections()
        for socket in connections:
            socket.close()

        self.socket.close()
        self.listener_socket.close()
        sys.exit()

    def handle_error_server(self, error):
        if error == errno.ECONNREFUSED:
            error_message = 'Looks like the server is unavailable at the moment. Try again later.'

        elif error == errno.ECONNABORTED:
            error_message = 'There was a problem connecting to the server, try again.'

        elif error == errno.ECONNRESET:
            error_message = 'It seems the connection is down. Try again later.'

        return error_message


    def connect_to_chat(self, name):     
        connect_chat_request = MessageMapper.pack_connect_request(name, LISTENER_SOCKET_HOST, self.listener_socket.getsockname()[1])
        
        try:
            self.send(self.socket, connect_chat_request)

            connection_response: bytes = self.socket.recv(MAX_MESSAGE_SIZE_RECV)
            status: int = MessageMapper.unpack_status(connection_response[8:9])

            if status == Status.OK.value:
                global my_name 
                my_name = name.lower()
                return (True, '')

            else:
                message = connection_response[9:]
                error_message = MessageMapper.unpack_error_response(message)
                return (False, error_message)

        except OSError as error:
            error_message = 'Failed to send message to server. Try again.\nOS error: {0}'.format(error)
            return (False, error_message)


    def accept_new_peer(self):
        try:
            client_sock, address, user_name = self.accept_connection(self.listener_socket)
            print('Connected with: ', address)

            connections_lister.add_connection(user_name, client_sock)
            peers_lister.add_to_peers(user_name)
            return (True, user_name, client_sock)

        except OSError as error:
            return (False, 'OS error: {0}'.format(error), None)


    def accept_connection(self, socket):
        try:
            (client_socket, address) = socket.accept()
            message = client_socket.recv(MAX_MESSAGE_SIZE_RECV)
            user_name = MessageMapper.unpack_user_id_on_connect_message(message[8:])
            return (client_socket, address, user_name)
        
        except OSError:
            raise

    def receive(self, client_sock):
        message = client_sock.recv(MAX_MESSAGE_SIZE_RECV)

        if not message:
            name = connections_lister.pop_connection_by_socket(client_sock)[0]
            if name:
                peers_lister.remove_from_peers(name)
                message = name + ' disconnected'
                return (False, message, None, client_sock)

        (user, msg) = MessageMapper.unpack_message_receive(message)
        return (True, msg, user, None)

    def send(self, socket, msg):
        try:
            socket.sendall(msg)  
        except OSError:
            raise

    def handle_server_message(self):
        try:
            message = self.socket.recv(MAX_MESSAGE_SIZE_RECV)
            method = MessageMapper.unpack_method(message)
            if method == Method.VALIDATE_CONNECTION.value:
                self.handle_validation(self.socket)
                return (True, None)

        except (ConnectionResetError, ConnectionAbortedError):
            error_message = 'Server disconnected'
            self.disconnect_from_chat()
            return (False, error_message)

        except OSError as error:
            message = 'OS error: {0}'.format(error) + ', try again'
            return (False, message)

    def handle_validation(self, socket):
        response = MessageMapper.pack_ok_response(Method.VALIDATE_CONNECTION.value)
        try:
            self.send(socket, response)
        
        except OSError:
            raise


    def get_user_list(self):
        get_list_request = MessageMapper.pack_get_list_request()
        try:
            self.send(self.socket, get_list_request)
            get_list_response = self.socket.recv(MAX_MESSAGE_SIZE_RECV)
            user_list = MessageMapper.unpack_get_list_response(get_list_response[9:])
            return (True, user_list, None)
        
        except (ConnectionResetError, ConnectionAbortedError):
            error_message = 'Server disconnected'
            self.disconnect_from_chat()
            return (False, None, error_message)

        except OSError as error:
            message = 'OS error: {0}'.format(error) + ', try again'
            return (False, None, message)


    def connect_with_user(self, name):
        if name == my_name:
            error_message = 'You can\'t connect to yourself, try another user :)'
            return (False, error_message, None)

        else:
            if peers_lister.exists_in_peers(name):
                error_message = 'You are already connected to ' + name + ', try another user :)'
                return (False, error_message, None)

        get_user_request = MessageMapper.pack_get_user_request(name)

        try: 
            self.send(self.socket, get_user_request)
            get_user_response = self.socket.recv(MAX_MESSAGE_SIZE_RECV)

            status = MessageMapper.unpack_status(get_user_response[8:9])
            message = get_user_response[9:]

            if status == Status.OK.value:
                user: User = MessageMapper.unpack_get_user_response(message)

                new_socket = sock.socket()
                success, message = self.connect(new_socket, user)
                if not success:
                    return (success, message, None)

                connections_lister.add_connection(user.name, new_socket)
                peers_lister.add_to_peers(user.name)

                return (True, None, new_socket)

            else:
                error_message = MessageMapper.unpack_error_response(message)
                return (False, error_message, None)

        except (ConnectionResetError, ConnectionAbortedError):
            error_message = 'Server disconnected'
            self.disconnect_from_chat()
            return (False, error_message, None)

        except OSError as error:
            error_message = 'Failed to send message\nOS error: {0}'.format(error) + '\nIf the error persists, consider disconnecting'
            return (False, error_message, None)
    

    def connect(self, socket, user: User):
        try:
            socket.connect((user.ip_address, user.port))

        except OSError as error:
            error_message = 'Failed to connect to ' + user.name + '\nOS error: {0}'.format(error)
            self.disconnect_from_user(user.name)
            self.check_user(user.name)
            return (False, error_message)

        id_msg = MessageMapper.pack_user_id_on_connect_message(my_name)

        try:
            self.send(socket, id_msg)
            return (True, None)

        except OSError as error:
            error_message = 'Failed to connect to ' + user.name + '\nOS error: {0}'.format(error)
            self.disconnect_from_user(user.name)
            self.check_user(user.name)
            return (False, error_message)       

    def send_input_message_to_user(self, name, user_input):
        if name == my_name:
            error_message = 'You can\'t send a message to yourself, try someone else in the chat :)'
            return (False, error_message)

        else:
            if not peers_lister.exists_in_peers(name):
                error_message = 'You are not connected to' + name + '\nYou can\'t send a message to a user you are not connected to.'
                return (False, error_message)

        message = MessageMapper.pack_message_send(my_name, user_input)
        client_socket = connections_lister.get_connection_by_name(name)
        
        try:
            self.send(client_socket, message)
            return (True, '')
        
        except OSError as error:
            error_message = 'Failed to send message to ' + name + '\nOS error: {0}'.format(error) + '\nIf the error persists, consider disconnecting from user'
            self.check_user(name)
            return (False, error_message)


    def check_user(self, name):
        check_user_request = MessageMapper.pack_check_user_request(name)
        self.send(self.socket, check_user_request)


    def get_peers_list(self):
        if peers_lister.is_empty():
            return (False, '')
        else: 
            peers_list = peers_lister.get_peers()
            return (True, peers_list)


    def disconnect_from_user(self, name):
        if not peers_lister.exists_in_peers(name):
            error_message = 'You can\'t disconnect from a user you are not connected to.'
            return (False, error_message, None)

        client_socket = connections_lister.pop_connection_by_name(name)
        peers_lister.remove_from_peers(name)

        client_socket.close()
        message = 'Disconnected from ' + name
        return (True, message, client_socket)

    def get_chat_name(self):
        return my_name
