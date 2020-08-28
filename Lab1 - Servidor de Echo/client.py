import socket

HOST: str = 'localhost'
PORT: int = 5000

socket = socket.socket()

socket.connect((HOST, PORT))

while True:
    message: str = input()

    if message.lower() == "close": 
        break
    else:
        socket.send(message.encode('utf-8'))

        received_message = socket.recv(1024)
        print(str(received_message, encoding='utf-8'))

socket.close()