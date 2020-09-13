import socket as sock
import json

HOST: str = 'localhost'
PORT: int = 5000

def display(data: dict, minCountSize: int = 4, wordLenght: int = 28):
    print('\nWORD                        COUNT\n')
    for x in data:
        c = data[x]
        count = str(c)
        while c < 10**(minCountSize - 1):
            count = '0' + count
            c *= 10

        word = x
        while len(word) < wordLenght: 
            word += '_'
        
        print(word + count)

def main():
    # socket initialization (using the default internet address family and stream socket type)  
    socket = sock.socket()

    # connects with server
    socket.connect((HOST, PORT))

    print('\nType the text file name you want to analyze in the format \'test.txt\'.\nTo close the connection, send \'close\'.')


    # waits for user input and transmits it to server until user decides to close the connection
    while True:

        fileName: str = input("\n~> ")

        # check if user wants to close the connection
        if fileName.lower() == "close": 
            break
        else:
            socket.send(fileName.encode('utf-8'))

            # receives answer from server, decodes it and prints it on console
            received_message = socket.recv(4096)

            try:
                res = json.loads(str(received_message, encoding='utf-8'))
                display(res, 4, 28)

            except json.decoder.JSONDecodeError:
                print(str(received_message, encoding='utf8'))


    # closes the connection
    socket.close()

if __name__ == "__main__":
    main()
