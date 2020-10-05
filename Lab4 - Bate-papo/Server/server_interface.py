from server_controller import ServerController
import select
import sys

class ServerInterface:

    inputs = [sys.stdin]
    
    def main(self):
        controller = ServerController()
        socket = controller.socket

        self.inputs.append(socket)

        print('Server Ready...\nType /close to terminate server execution')
        
        while True:
            r, w, err = select.select(self.inputs, [], [])

            for read in r:
                if read == socket:
                    success, message = controller.accept_new_peer()
                    if not success:
                        self.show_error(message)

                    else:
                        print('Connected with: ', message)

                elif read == sys.stdin: 
                    command = input()
                    if command == '/close':
                        controller.close_server()

                    else:
                        print('Command not found.')

    
    def show_error(self, error_message):
        print('Oops, seems like something went wrong :(')
        print(error_message)