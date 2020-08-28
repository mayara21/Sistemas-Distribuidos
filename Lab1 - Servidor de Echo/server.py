import socket

HOST: str = ''
PORT: int = 5000

socket = socket.socket()

socket.bind((HOST, PORT))

socket.listen(1)

newSocket, address = socket.accept()

while True:
    message = newSocket.recv(1024)

    if not message: 
        break
    else:
        newSocket.send(message)

newSocket.close()

socket.close()