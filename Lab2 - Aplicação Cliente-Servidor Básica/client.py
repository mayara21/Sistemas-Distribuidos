import socket

HOST: str = 'localhost'
PORT: int = 5000
    
# socket initialization (using the default internet address family and stream socket type)  
socket = socket.socket()

# connects with server
socket.connect((HOST, PORT))

print('Type the text file name you want to analyze in the format \'test.txt\'.\nTo close the connection, send \'close\'.')

# waits for user input and transmits it to server until user decides to close the connection
while True:
    fileName: str = input()

    # check if user wants to close the connection
    if fileName.lower() == "close": 
        break
    else:
        socket.send(fileName.encode('utf-8'))

        # receives answer from server, decodes it and prints it on console
        received_message = socket.recv(4096)
        print(str(received_message, encoding='utf-8'))

# closes the connection
socket.close()
