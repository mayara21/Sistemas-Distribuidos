import threading
import socket as sock
import select
import sys
from user import User
from method import Method
from status import Status
from message_mapper import Message_Mapper

SERVER_HOST: str = '127.0.0.1'
SERVER_PORT: int = 9000

LISTENER_SOCKET_HOST: str = '127.0.0.1'

MAX_MESSAGE_SIZE_RECV = 4096

inputs = [sys.stdin]

my_name = ''

connections: dict = {}

def init_listener():
    socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    socket.bind((LISTENER_SOCKET_HOST, 0))

    socket.listen(5)
    socket.setblocking(False)

    inputs.append(socket)

    return socket


def accept_conection(socket):
    (client_socket, address) = socket.accept()
    print(client_socket, address)

    msg = client_socket.recv(MAX_MESSAGE_SIZE_RECV)

    user_name = Message_Mapper.unpack_user_id_on_connect_message(msg[8:])

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
                        socket.close()

                        print(name + ' closed')
                        return

            (user, msg) = Message_Mapper.unpack_message_receive(message)

            print('(' + user + '): ' + msg)

        else:
            if shutdown_event.is_set():
                client_sock.close()
                return


def connect(socket, user_ip, user_port, shutdown_event: threading.Event):
    socket.connect((user_ip, user_port))
    id_msg = Message_Mapper.pack_user_id_on_connect_message(my_name)

    send(socket, id_msg)

    receive(socket, shutdown_event)


def send_to_user(name, user_input):
    message = Message_Mapper.pack_message_send(my_name, user_input)
    client_socket, thread, shutdown_event = connections[name]
    send(client_socket, message)


def send(socket, msg):
    socket.sendall(msg)  

def connect_to_chat(socket, listener_socket):
    while True:
        name: str = input('Enter the name you want to use in the chat\n(if you want to quit, enter leave): ')

        if (name.lower() == 'leave'):
            socket.close()
            listener_socket.close()
            sys.exit() 
            
        connect_chat_request = Message_Mapper.pack_connect_request(name, LISTENER_SOCKET_HOST, listener_socket.getsockname()[1])
        send(socket, connect_chat_request)

        connection_response: bytes = socket.recv(MAX_MESSAGE_SIZE_RECV)
        status: int = Message_Mapper.unpack_status(connection_response[8:9])

        if status == Status.OK.value:
            global my_name 
            my_name = name.lower()
            break

        else:
            message = connection_response[9:]
            error_message = Message_Mapper.unpack_error_response(message)
            show_error(error_message)


def handle_validation(socket):
    response = Message_Mapper.pack_ok_response(Method.VALIDATE_CONNECTION.value)
    send(socket, response)


def disconnect_from_chat():
    for (socket, thread, shutdown_event) in connections.values():
        shutdown_event.set()
        thread.join()
        socket.close()

    sys.exit()


def show_list(user_list):
    user_list.remove(my_name) # add try exception
    if len(user_list) == 0:
        print('There are no users currently connected to the chat :(\nTry again later')

    else:
        print(user_list)


def get_user_list(socket):
    get_list_request = Message_Mapper.pack_get_list_request()
    send(socket, get_list_request)

    get_list_response = socket.recv(MAX_MESSAGE_SIZE_RECV)

    user_list = Message_Mapper.unpack_get_list_response(get_list_response[9:])
    show_list(user_list)


def connect_with_user(socket, name):
    get_user_request = Message_Mapper.pack_get_user_request(name)

    send(socket, get_user_request)
    get_user_response = socket.recv(MAX_MESSAGE_SIZE_RECV)

    status = Message_Mapper.unpack_status(get_user_response[8:9])
    message = get_user_response[9:]

    if status == Status.OK.value:
        user: User = Message_Mapper.unpack_get_user_response(message)

        new_socket = sock.socket()
        shutdown_event = threading.Event()
        client = threading.Thread(target=connect, args=(new_socket, user.ip_address, user.port, shutdown_event))
        connections[user.name] = (new_socket, client, shutdown_event)

        client.start()

    else:
        error_message = Message_Mapper.unpack_error_response(message)
        show_error(error_message)


def check_user(socket, name):
    check_user_request = Message_Mapper.pack_check_user_request(name)
    send(socket, check_user_request)


def disconnect_from_user(name):
    client_socket, thread, shutdown_event = connections.pop(name)

    shutdown_event.set()
    thread.join()
    client_socket.close()


def show_instructions(): 
    print('Chat instructions:')
    print('- \'/help\': list chat instructions')
    print('- \'/list\': list active users')
    print('- \'/connect user\': connect to user')
    print('- \'/send user message\': send message to specified user')
    print('- \'/disconnect user\': disconnect from user')
    print('- \'/leave\': disconnect from chat')


def show_error(error_message):
    print('Oops, seems like something went wrong :(')
    print(error_message)


def main():
    socket = sock.socket()
    socket.connect((SERVER_HOST, SERVER_PORT))
    inputs.append(socket)
    listener_socket = init_listener()

    connect_to_chat(socket, listener_socket)

    print('Welcome to the chat!')
    show_instructions()

    while True:
        r, w, err = select.select(inputs, [], [])

        for read in r:
            if read == listener_socket:
                client_sock, address, user_name = accept_conection(listener_socket)
                print('Connected with: ', address)

                shutdown_event = threading.Event()
                client = threading.Thread(target=receive, args=[client_sock, shutdown_event])

                connections[user_name] = (client_sock, client, shutdown_event)
                client.start()

            elif read == socket:
                message = socket.recv(MAX_MESSAGE_SIZE_RECV)
                method = Message_Mapper.unpack_method(message)
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
                    connect_with_user(socket, name)

                elif head == '/check':
                    name = request[1]
                    check_user(socket, name)

                elif head == '/send':
                    name = request[1]
                    message = ' '.join(request[2:])
                    send_to_user(name, message)

                elif head == '/disconnect':
                    name = request[1]
                    disconnect_from_user(name)

                elif head == '/help':
                    show_instructions()

                else:
                    print('Command not found. Enter \'/help\' to see available commands.')                

if __name__ == "__main__":
    main()