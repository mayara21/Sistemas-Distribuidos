import socket

HOST: str = 'localhost'
PORT: int = 5000
    
# socket initialization (using the default internet address family and stream socket type)  
socket = socket.socket()

# connects with server
socket.connect((HOST, PORT))

print('Connected with server!\nType the text file name you want to analyze.\n')

# waits for user input and transmits it to server until user decides to close the connection

while True:
    fileName: str = input()

    if fileName.lower() == "close": 
        break
    else:
        socket.send(fileName.encode('utf-8'))

        received_message = socket.recv(1024)
        print(str(received_message, encoding='utf-8'))

# closes the connection
socket.close()
