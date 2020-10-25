import socket as sock
import sys
import select
import multiprocessing
import rpyc
from node import Node

HOST: str = ''
PORT: int = 5000

inputs = [sys.stdin]

ring = []
clients = []

def insert(originNode, key, value):
    node = ring[originNode]
    print('no origem: ', node.address, node.port, node.id)
    connection = rpyc.connect(node.address, node.port)

    print(type(connection.root))
    print(connection.root.get_service_name())

    connection.root.exposed_insert_key(key, value)
    connection.close()

def search(searchId, originNode, key):
    resultNode = None
    return resultNode


def start():
    for node in ring:
        client = multiprocessing.Process(target=node.start)
        client.start()
        clients.append(client)


def create_ring(quant):
    ring_size = pow(2, quant)

    for id in range (ring_size):
        ring.append(Node(id, '', PORT + id + 1))

    for id in range (ring_size):
        node: Node = ring[id]
        successor: Node = ring[id + 1] if (id + 1 < ring_size) else ring[0]
        node.set_successor(successor)

        finger = []
        for k in range (1, quant + 1):
            value: int = (id + pow(2, k - 1)) % ring_size
            finger.append(ring[value])

        node.set_finger_table(finger)

    start()
        

def main():
    
    quant = input('Insert N: ') # insert originNode key value
    create_ring(int(quant))

    while True:
        command = input()
        request = command.split(' ')
        head = request[0]
        request_size = len(request)

        if command == 'close':
            for c in clients: 
                c.join()
            sys.exit()
            break

        elif head == 'insert' and request_size > 3:
            origin = int(request[1])
            key = request[2]
            value = ' '.join(request[3:])

            insert(origin, key, value)

        elif head == 'search' and request_size > 2:
            origin = request[1]
            key = request[2]

            # search(origin, key)


if __name__ == "__main__":
    main()
        