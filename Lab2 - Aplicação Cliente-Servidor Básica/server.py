import socket as sock
import json

HOST: str = ''
PORT: int = 5000
ERROR_MESSAGE: str = "File not found."
TOP_ITENS_SIZE: int = 10

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


def main():
    # socket initialization (using the default internet address family and stream socket type) and binding
    socket = sock.socket()
    socket.bind((HOST, PORT))

    # awaits for a connection and stablishes a maximum of 1 pending connection
    socket.listen(1)
    
    while True:
        # accepts first connection
        new_socket, address = socket.accept()

        print('Connected with: ', address)

        # keeps the connection and message trading until client decides to close it
        while True:
            file_name = new_socket.recv(4096)

            # if client wants to close the connection, breaks the loop
            if not file_name: 
                break

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
                new_socket.send(data.encode())

            # if file is not found, send an error message to client
            except FileNotFoundError:
                new_socket.send(ERROR_MESSAGE.encode('utf-8'))

        # closes connection socket
        new_socket.close()

    socket.close()

if __name__ == "__main__":
    main()