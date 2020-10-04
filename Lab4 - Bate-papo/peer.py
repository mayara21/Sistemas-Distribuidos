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
LISTENER_SOCKET_PORT: int = 12000

inputs = [sys.stdin]

my_name = ''

connections: dict = {}

def init_listener():
    socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    socket.bind((LISTENER_SOCKET_HOST, LISTENER_SOCKET_PORT))

    socket.listen(5)
    socket.setblocking(False)

    inputs.append(socket)

    return socket


def accept_conection(socket):
    (client_socket, address) = socket.accept()
    print(client_socket, address)

    msg = client_socket.recv(4096)

    user_name = Message_Mapper.unpack_user_id_on_connect_message(msg[8:])

    return (client_socket, address, user_name)


def receive(client_sock, shutdown_event: threading.Event):
    client_sock.setblocking(False)
    while True:
        ready = select.select([client_sock], [], [], 1)[0]

        if ready:
            message = client_sock.recv(4096)

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
    print('Conecting to ' + user_ip + ' ' + str(user_port))

    socket.connect((user_ip, user_port))
    id_msg = Message_Mapper.pack_user_id_on_connect_message(my_name)

    send(socket, id_msg)

    receive(socket, shutdown_event)


def send(socket, msg):
    socket.sendall(msg)        


def main():
    socket = sock.socket()
    socket.connect((SERVER_HOST, SERVER_PORT))

    listener_socket = init_listener()


    while True:
        name: str = input('Enter the name you want to use in the chat: ')

        if (name.lower() == 'close'): 
            break
            
        connect_chat_request = Message_Mapper.pack_connect_request(name, LISTENER_SOCKET_HOST, LISTENER_SOCKET_PORT)
        socket.sendall(connect_chat_request)

        connection_response = socket.recv(4096)
            
        status: int = Message_Mapper.unpack_status(connection_response[8:9])

        if status == Status.OK.value:
            global my_name 
            my_name = name.lower()
            break

        else:
            message = connection_response[9:]
            error_message = Message_Mapper.unpack_error_response(message)
            print(error_message)

    print('Connected to chat!...\nType /close to terminate execution')

    # add instructions!!

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

            elif read == sys.stdin: 
                cmd = input()
                if cmd == '/close':

                    for (socket, thread, shutdown_event) in connections.values():
                        shutdown_event.set()
                        thread.join()
                        socket.close()

                    sys.exit()

                request = cmd.split(' ')

                if request[0].lower() == '/list':
                    get_list_request = Message_Mapper.pack_get_list_request()
                    socket.sendall(get_list_request)

                    get_list_response = socket.recv(4096)

                    user_list = Message_Mapper.unpack_get_list_response(get_list_response[9:])
                    print (user_list)


                elif request[0].lower() == '/connect':
                    name = request[1]

                    get_user_request = Message_Mapper.pack_get_user_request(name)
                    socket.sendall(get_user_request)

                    get_user_response = socket.recv(4096)
                    status = Message_Mapper.unpack_status(get_user_response[8:9])
                    message = get_user_response[9:]

                    if status == Status.OK.value:
                        user = Message_Mapper.unpack_get_user_response(message)

                        new_socket = sock.socket()
                        shutdown_event = threading.Event()
                        client = threading.Thread(target=connect, args=(new_socket, user.ip_address, user.port, shutdown_event))
                        connections[user.name] = (new_socket, client, shutdown_event)

                        client.start()

                    else:
                        error_message = Message_Mapper.unpack_error_response(message)
                        print(error_message)

                
                elif request[0].lower() == '/check':
                    user_name = request[1]
                    check_user_request = Message_Mapper.pack_check_user_request(user_name)

                    socket.sendall(check_user_request)


                elif request[0] == '/send':
                    # ipdb.set_trace()
                    name = request[1]
                    message = ' '.join(request[2:])

                    msg = Message_Mapper.pack_message_send(my_name, message)
                    client_socket, thread, shutdown_event = connections[name]
                    send(client_socket, msg)

                elif request[0] == '/disconnect':
                    name = request[1]
                    client_socket, thread, shutdown_event = connections.pop(name)

                    shutdown_event.set()
                    thread.join()
                    client_socket.close()
                
            

if __name__ == "__main__":
    main()