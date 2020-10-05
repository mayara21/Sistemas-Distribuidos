import socket as sock
import select
import sys
from user import User
from peer_controller import PeerController
from peer_connections_lister import connections_lister

class PeerInterface:
    inputs = [sys.stdin]

    def show_list(self, user_list, my_name):
        user_list.remove(my_name)
        if len(user_list) == 0:
            print('There are no users currently connected to the chat :(\nTry again later')

        else:
            print('Here are the available users, try connecting with someone :)')
            for name in user_list:
                print(name)


    def show_peers(self, user_list):
        print('You are connected to: ')
        for name in user_list:
            print(name)


    def show_instructions(self): 
        print('Chat instructions:')
        print('- \'/help\': list chat instructions')
        print('- \'/name\': show the name you are using')
        print('- \'/list\': list active users')
        print('- \'/connect user\': connect to user')
        print('- \'/connections\': list the users you are connected to')
        print('- \'/send user message\': send message to specified user')
        print('- \'/disconnect user\': disconnect from user')
        print('- \'/leave\': disconnect from chat')


    def show_error(self, error_message):
        print('Oops, seems like something went wrong :(')
        print(error_message)


    def show_your_message(self, name, user_input):
        print('(you to ' + name + '): ' + user_input)

    def show_message(self, name, message):
        print('(' + name + '): ' + message)

    def connect_to_chat(self, controller):
        while True:
            name: str = input('Enter the name you want to use in the chat\n(if you want to quit, enter leave): ')
            if name.lower() == 'leave':
                controller.disconnect_from_chat()
            
            success, message = controller.connect_to_chat(name)
            if not success:
                self.show_error(message)
            else:
                print('Hello, ' + name + '! Welcome to the chat!')
                self.show_instructions()
                break


    def main(self):
        controller = PeerController()
        socket = controller.socket
        listener_socket = controller.listener_socket

        success, message = controller.connect_server()
        if not success:
            self.show_error(message)
            controller.disconnect_from_chat()
        
        success, message = controller.init_listener_socket()
        if not success:
            self.show_error(message)
            controller.disconnect_from_chat()

        self.inputs.append(socket)
        self.inputs.append(listener_socket)

        self.connect_to_chat(controller)

        while True:
            try:
                r, w, err = select.select(self.inputs, [], [])
                for read in r:
                    if read == listener_socket:
                        success, message, client_socket = controller.accept_new_peer()

                        if success:
                            print('Connected with ' + message)
                            self.inputs.append(client_socket)
                        else:
                            self.show_error(message)

                    elif read == socket:
                        controller.handle_server_message()

                    elif connections_lister.contains(read):
                        success, message, user, client_socket = controller.receive(read)

                        if not success:
                            print(message)                          
                            self.inputs.remove(client_socket)
                            client_socket.close()
                        else:
                            self.show_message(user, message)

                    elif read == sys.stdin: 
                        cmd = input()
                        request = cmd.split(' ')
                        head = request[0].lower()

                        if head == '/leave':
                            controller.disconnect_from_chat()

                        elif head == '/list':
                            success, user_list = controller.get_user_list()
                            if success:
                                name = controller.get_chat_name()
                                self.show_list(user_list, name)
                            else:
                                message = 'There was as error in the process, try again'
                                self.show_error(message)

                        elif head == '/connect':
                            name = request[1]
                            success, message, client_socket = controller.connect_with_user(name)
                            if success:
                                print('Connected with ' + name)
                                self.inputs.append(client_socket)
                            else:
                                self.show_error(message)

                        elif head == '/send':
                            name = request[1]
                            message = ' '.join(request[2:])
                            success, return_message = controller.send_input_message_to_user(name, message)
                            if success:
                                self.show_your_message(name, message)
                            else:
                                self.show_error(return_message)

                        elif head == '/connections':
                            success, user_list = controller.get_peers_list()
                            if not success:
                                error_message = 'It seems you are not connected with anyone :(\nTry \'/list\' to see active users.'
                                self.show_error(error_message)
                            else:
                                self.show_peers(user_list)

                        elif head == '/disconnect':
                            name = request[1]
                            success, message, client_socket = controller.disconnect_from_user(name)
                            if success:
                                self.inputs.remove(client_socket)
                                print(message)
                            else:
                                self.show_error(message)

                        elif head == '/name':
                            name = controller.get_chat_name()
                            print('Your name in the chat is: ' + name)

                        elif head == '/help':
                            self.show_instructions()

                        else:
                            print('Command not found. Enter \'/help\' to see available commands.')

            except KeyboardInterrupt:
                controller.disconnect_from_chat()
