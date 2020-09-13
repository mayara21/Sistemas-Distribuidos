import socket as sock
import json
import sys
import select
import multiprocessing

# stablishes server location
HOST: str = ''
PORT: int = 5000

# constants
ERROR_MESSAGE: str = "File not found."
TOP_ITENS_SIZE: int = 10

# defines list of I/O the server is interested in (including the standard input)
inputs = [sys.stdin]

# function for counting the words on file content, using a dictionary
def text_processing(content: str):
    dictionary = {}

    for word in content.lower().split(" "):

        # removes ponctuation
        if word in ['!', '.', ',', ';', '@', '#', '$', '%', '^', '~', '&', '(', ')', '-', '+', '=', '_', '\"', '\'', ':', '>', '<', '?', '/', '\\', '|', '', '\n', '[', ']', '{', '}']:
            continue
        
        if word not in dictionary:
            dictionary[word] = 1
        else:
            dictionary[word] += 1
    
    return dictionary

# function for sorting the dictionary in descending order and return a dictionary containing the top n itens
def sort_top_itens(dictionary: dict):
    top_itens = {}
    sorted_list = sorted(dictionary, key = dictionary.get, reverse = True)

    for word in sorted_list[:TOP_ITENS_SIZE]:
        top_itens[word] = dictionary[word]

    return top_itens

def init_server():
     # socket initialization (using the default internet address family and stream socket type) and binding
    socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    socket.bind((HOST, PORT))

    # waits for a connection and stablishes a maximum of 5 pending connection
    socket.listen(5)

    # sets socket to non-blocking mode
    socket.setblocking(False)

    # includes socket in list of inputs that should be listened to
    inputs.append(socket)

    return socket

# accepts connection requests from a client
def accept_conection(socket):
    client_sock, address = socket.accept()

    return client_sock, address

# deals with the connection with a client, receiving messages and sending responses to the client
def serve(client_sock, address):
    # keeps the connection and message trading until client decides to close it
    while True:

        file_name = client_sock.recv(4096)

        # if client wants to close the connection
        if not file_name:
            print('> Client ' + str(address) + ' disconnected') 
            # closes connection socket
            client_sock.close()
            return
        
        print('> Client ' + str(address) + ' requested file named ' + str(file_name, encoding='utf-8'))

        try:
            # open and read file, saving the content
            new_file_name = str(file_name, encoding='utf-8')
            txt_file = open(new_file_name, 'r', encoding='utf-8')
            content = txt_file.read()
            txt_file.close()
            
            # counts the words in content and stablishes the top itens
            dictionary = text_processing(content)
            top_itens = sort_top_itens(dictionary)
        
            # serializes the dictionary in a json, and sends it to client
            data = json.dumps(top_itens, ensure_ascii=False)
            client_sock.send(data.encode())

        # if file is not found, send an error message to client
        except FileNotFoundError:
            print('> ' + str(address) + ': File ' + str(file_name, encoding='utf-8') + ' Could not be found')
            client_sock.send(ERROR_MESSAGE.encode('utf-8'))

def main():
    clients = [] # saves the created processes to join them
    socket = init_server()
    print('Server Ready...\nType close to terminate server execution')
    
    while True:
        # awaits any inputs of interest 
        r, w, err = select.select(inputs, [], [])
        for read in r:
            if read == socket: # new client connection request
                client_sock, address = accept_conection(socket)
                print('Connected with: ', address)

                client = multiprocessing.Process(target=serve, args=(client_sock, address))
                client.start()

                clients.append(client) # saves process reference to use with join()

            elif read == sys.stdin: # command from terminal
                cmd = input()
                if cmd == 'close':
                    for c in clients: # waits for all the process to end
                        c.join()

                    socket.close() # closes main socket
                    sys.exit()

if __name__ == "__main__":
    main()