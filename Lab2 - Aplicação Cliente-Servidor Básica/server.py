import socket

HOST: str = ''
PORT: int = 5000

ERROR_MESSAGE: str = "File not found."

# socket initialization (using the default internet address family and stream socket type) and binding
socket = socket.socket()
socket.bind((HOST, PORT))

# awaits for a connection and stablishes a maximum of 5 pending connection
socket.listen(5)

# accepts first connection
newSocket, address = socket.accept()

print('Connected with: ', address)

# keeps the connection and message trading until client decides to close it
while True:
    fileName = newSocket.recv(1024)

    if not fileName: 
        break

    try:
        txtFile = open(str(fileName, encoding='utf-8'), 'r')
        content = txtFile.read()
        
        txtFile.close()
    except FileNotFoundError:
        newSocket.send(ERROR_MESSAGE.encode('utf-8'))

    else:
        newSocket.send(b'tudo certo')

# closes connection and main socket
newSocket.close()
socket.close()