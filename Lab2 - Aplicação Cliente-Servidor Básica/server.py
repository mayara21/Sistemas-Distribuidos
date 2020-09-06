import socket as sock
import json

HOST: str = ''
PORT: int = 5000
ERROR_MESSAGE: str = "File not found."
TOP_ITENS_SIZE: int = 10

def text_processing(content: str):
    dictionary = {}

    for word in content.lower().split(" "):
        word = word.replace(".","").replace(",","").replace(":","").replace("\"","").replace("!","").replace("?","").replace("*","")
        
        if word not in dictionary:
            dictionary[word] = 1
        else:
            dictionary[word] += 1
    
    return dictionary

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

    # awaits for a connection and stablishes a maximum of 5 pending connection
    socket.listen(5)

    # keeps the connection and message trading until client decides to close it
    while True:
        # accepts first connection
        new_socket, address = socket.accept()

        print('Connected with: ', address)

        while True:
            file_name = new_socket.recv(4096)

            if not file_name: 
                break

            try:
                new_file_name = str(file_name, encoding='utf-8')
                txt_file = open(new_file_name, 'r', encoding='utf-8')
                content = txt_file.read()
                txt_file.close()
                
                dictionary = text_processing(content)
                top_itens = sort_top_itens(dictionary)
            
                data = json.dumps(top_itens, ensure_ascii=False)
                new_socket.send(data.encode())

            except FileNotFoundError:
                new_socket.send(ERROR_MESSAGE.encode('utf-8'))

        # closes connection socket
        new_socket.close()
        
    socket.close()

if __name__ == "__main__":
    main()