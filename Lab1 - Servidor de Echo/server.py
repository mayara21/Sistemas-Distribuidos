import socket

HOST: str = ''
PORT: int = 5000

# socket initialization (using the default internet address family and stream socket type) and binding
socket = socket.socket()
socket.bind((HOST, PORT))

# awaits for a connection and stablishes a maximum of 1 pending connection
socket.listen(1)

# accepts first connection
newSocket, address = socket.accept()

print('Connected with: ', address)

# keeps the connection and message trading until client decides to close it
while True:
    message = newSocket.recv(1024)

    if not message: 
        break
    else:
        newSocket.send(message)

# closes connection and main socket
newSocket.close()
socket.close()
