import errno
import threading
import socket as sock
import select
import sys
from user import User
from method import Method
from status import Status
from message_mapper import MessageMapper

SERVER_HOST: str = '127.0.0.1'
SERVER_PORT: int = 9000

LISTENER_SOCKET_HOST: str = '127.0.0.1'

MAX_MESSAGE_SIZE_RECV = 4096

inputs = [sys.stdin]

my_name = ''

connections: dict = {}
peers = []

def init_listener():
    socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    try:
        socket.bind((LISTENER_SOCKET_HOST, 0))

    except OSError as error:
        print("OS error: {0}".format(error))
        socket.close()
        sys.exit()

    socket.listen(5)
    socket.setblocking(False)

    inputs.append(socket)

    return socket


def accept_conection(socket):
    (client_socket, address) = socket.accept()

    msg = client_socket.recv(MAX_MESSAGE_SIZE_RECV)

    user_name = MessageMapper.unpack_user_id_on_connect_message(msg[8:])

    return (client_socket, address, user_name)


def receive(client_sock, shutdown_event: threading.Event):
    client_sock.setblocking(False)

    while True:
        ready = select.select([client_sock], [], [], 1)[0]

        if ready:
            message = client_sock.recv(MAX_MESSAGE_SIZE_RECV)

            if not message:
                aux = connections
                for name, (socket, thread, event) in aux.items():
                    if socket == client_sock:
                        connections.pop(name)
                        peers.remove(name)
                        socket.close()

                        print(name + ' closed')
                        return

            (user, msg) = MessageMapper.unpack_message_receive(message)

            print('(' + user + '): ' + msg)

        else:
            if shutdown_event.is_set():
                client_sock.close()
                return


def connect(socket, user: User, shutdown_event: threading.Event):
    try:
        socket.connect((user.ip_address, user.port))

    except OSError as error:
        print('Failed to connect to ' + user.name + '\nOS error: {0}'.format(error))
        disconnect_from_user(user.name)
        check_user(socket, user.name)
        return

    id_msg = MessageMapper.pack_user_id_on_connect_message(my_name)

    try:
        send(socket, id_msg)

    except OSError as error:
        print('Failed to connect to ' + user.name + '\nOS error: {0}'.format(error))
        disconnect_from_user(user.name)
        check_user(socket, user.name)
        return       

    receive(socket, shutdown_event)

def send_input_message_to_user(name, user_input):
    message = MessageMapper.pack_message_send(my_name, user_input)
    client_socket, thread, shutdown_event = connections[name]
    try:
        send(client_socket, message)
        print('(you to ' + name + '): ' + user_input)
        # show_message(name, message)
    
    except OSError as error:
        print('Failed to send message to ' + name + '\nOS error: {0}'.format(error))
        print('If the error persists, consider disconnecting from user')
        # disconnect_from_user(name)
        check_user(client_socket, name)

def send(socket, msg):
    try:
        socket.sendall(msg)  
    except OSError:
        raise


def connect_to_chat(socket, listener_socket):
    while True:
        name: str = input('Enter the name you want to use in the chat\n(if you want to quit, enter leave): ')

        if (name.lower() == 'leave'):
            socket.close()
            listener_socket.close()
            sys.exit() 
            
        connect_chat_request = MessageMapper.pack_connect_request(name, LISTENER_SOCKET_HOST, listener_socket.getsockname()[1])
        try:
            send(socket, connect_chat_request)

            connection_response: bytes = socket.recv(MAX_MESSAGE_SIZE_RECV)
            status: int = MessageMapper.unpack_status(connection_response[8:9])

            if status == Status.OK.value:
                global my_name 
                my_name = name.lower()
                break

            else:
                message = connection_response[9:]
                error_message = MessageMapper.unpack_error_response(message)
                show_error(error_message)

        except OSError as error:
            print('Failed to send message to server. Try again.\nOS error: {0}'.format(error))


def handle_validation(socket):
    response = MessageMapper.pack_ok_response(Method.VALIDATE_CONNECTION.value)
    send(socket, response)


def disconnect_from_chat():
    for (socket, thread, shutdown_event) in connections.values():
        shutdown_event.set()
        thread.join()
        socket.close()

    sys.exit()


def show_list(user_list):
    user_list.remove(my_name)
    if len(user_list) == 0:
        print('There are no users currently connected to the chat :(\nTry again later')

    else:
        print(user_list)


def get_user_list(socket):
    get_list_request = MessageMapper.pack_get_list_request()
    send(socket, get_list_request)

    get_list_response = socket.recv(MAX_MESSAGE_SIZE_RECV)

    user_list = MessageMapper.unpack_get_list_response(get_list_response[9:])
    show_list(user_list)


def connect_with_user(socket, name):
    get_user_request = MessageMapper.pack_get_user_request(name)

    send(socket, get_user_request)
    get_user_response = socket.recv(MAX_MESSAGE_SIZE_RECV)

    status = MessageMapper.unpack_status(get_user_response[8:9])
    message = get_user_response[9:]

    if status == Status.OK.value:
        user: User = MessageMapper.unpack_get_user_response(message)

        new_socket = sock.socket()
        shutdown_event = threading.Event()
        client = threading.Thread(target=connect, args=(new_socket, user, shutdown_event))
        connections[user.name] = (new_socket, client, shutdown_event)
        peers.append(user.name)

        client.start()

    else:
        error_message = MessageMapper.unpack_error_response(message)
        show_error(error_message)


def check_user(socket, name):
    check_user_request = MessageMapper.pack_check_user_request(name)
    send(socket, check_user_request)


def disconnect_from_user(name):
    client_socket, thread, shutdown_event = connections.pop(name)
    peers.remove(name)

    shutdown_event.set()
    thread.join()
    client_socket.close()


def show_instructions(): 
    print('Chat instructions:')
    print('- \'/help\': list chat instructions')
    print('- \'/name\': show the name you are using')
    print('- \'/list\': list active users')
    print('- \'/connect user\': connect to user')
    print('- \'/connections\': list the users you are connected to')
    print('- \'/send user message\': send message to specified user')
    print('- \'/disconnect user\': disconnect from user')
    print('- \'/leave\': disconnect from chat')


def show_error(error_message):
    print('Oops, seems like something went wrong :(')
    print(error_message)


def handle_error_server(error):
    if error == errno.ECONNREFUSED:
        error_message = 'Looks like the server is unavailable at the moment. Try again later.'

    elif error == errno.ECONNABORTED:
        error_message = 'There was a problem connecting to the server, try again.'

    elif error == errno.ECONNRESET:
        error_message = 'It seems the connection is down. Try again later.'

    show_error(error_message)

def main():
    socket = sock.socket()

    try:
        socket.connect((SERVER_HOST, SERVER_PORT))

    except OSError as error:
        handle_error_server(error.errno)
        socket.close()
        sys.exit()

    inputs.append(socket)
    listener_socket = init_listener()

    connect_to_chat(socket, listener_socket)

    print('Welcome to the chat!')
    show_instructions()

    while True:
        try:
            r, w, err = select.select(inputs, [], [])

            for read in r:
                if read == listener_socket:
                    client_sock, address, user_name = accept_conection(listener_socket)
                    print('Connected with: ', address)

                    shutdown_event = threading.Event()
                    client = threading.Thread(target=receive, args=[client_sock, shutdown_event])

                    connections[user_name] = (client_sock, client, shutdown_event)
                    peers.append(user_name)
                    client.start()

                elif read == socket:
                    message = socket.recv(MAX_MESSAGE_SIZE_RECV)
                    method = MessageMapper.unpack_method(message)
                    if method == Method.VALIDATE_CONNECTION.value:
                        handle_validation(socket)

                elif read == sys.stdin: 
                    cmd = input()
                    request = cmd.split(' ')
                    head = request[0].lower()

                    if head == '/leave':
                        disconnect_from_chat()

                    elif head == '/list':
                        get_user_list(socket)

                    elif head == '/connect':
                        name = request[1]
                        if name == my_name:
                            error_message = 'You can\'t connect to yourself, try another user :)'
                            show_error(error_message)

                        else:
                            if peers.count(name) != 0:
                                error_message = 'You are already connected to ' + name + ', try another user :)'
                                show_error(error_message)

                            else:
                                connect_with_user(socket, name)

                    # elif head == '/check':
                    #     name = request[1]
                    #     check_user(socket, name)

                    elif head == '/send':
                        name = request[1]
                        if name == my_name:
                            error_message = 'You can\'t send a message to yourself, try someone else in the chat :)'
                            show_error(error_message)
                        else:
                            if peers.count(name) == 0:
                                error_message = 'You are not connected to' + name + '\nYou can\'t send a message to a user you are not connected to.'
                                show_error(error_message)

                            else:
                                message = ' '.join(request[2:])
                                send_input_message_to_user(name, message)

                    elif head == '/connections':
                        if len(peers) == 0:
                            print('It seems you are not connected with anyone :(\nTry \'/list\' to see active users.')
                        else: 
                            print(peers)

                    elif head == '/disconnect':
                        name = request[1]
                        if peers.count(name) == 0:
                            error_message = 'You can\'t disconnect from a user you are not connected to.'
                            show_error(error_message)

                        else:
                            disconnect_from_user(name)

                    elif head == '/name':
                        print('Your name in the chat is: ' + my_name)

                    elif head == '/help':
                        show_instructions()

                    else:
                        print('Command not found. Enter \'/help\' to see available commands.')

        except KeyboardInterrupt:
            disconnect_from_chat()

if __name__ == "__main__":
    main()