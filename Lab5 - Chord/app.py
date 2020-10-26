import socket as sock
import sys
import select
import multiprocessing
import rpyc
from node import Node

HOST: str = 'localhost'
PORT: int = 5000

inputs = [sys.stdin]

ring = []
clients = []
search_id_counter = 0

def insert(originNode, key, value):
    node = ring[originNode]
    connection = rpyc.connect(node.address, node.port)
    connection.root.exposed_insert_key(key, value)
    connection.close()


def print_search_result(search_id_counter, found_node_id, result):
    print('Search ' + str(search_id_counter) + ' found the value "' + str(result) + '" in node ' + str(found_node_id))


def search(originNode, key):
    global search_id_counter
    node = ring[originNode]

    connection = rpyc.connect(node.address, node.port)
    connection.root.exposed_search_key(print_search_result, key, search_id_counter)
    connection.close()

    search_id_counter += 1


def start():
    for node in ring:
        client = multiprocessing.Process(target=node.start)
        client.start()
        clients.append(client)


def create_ring(quant):
    ring_size = pow(2, quant)

    for id in range (ring_size):
        ring.append(Node(id, 'localhost', PORT + id + 1))

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
        

def print_instructions():
    print('To insert a key-value pair, type: ')
    print('insert origin_node_id key value')
    print('To search a key, type: ')
    print('search origin_node_id key')
    print('To get info about a node: ')
    print('info node_id')

def main():
    
    quant = input('Insert N: ')
    create_ring(int(quant))
    print('Ring created!')

    print_instructions()

    while True:
        command = input()
        request = command.split(' ')
        head = request[0]
        request_size = len(request)

        if command == 'close':
            for c in clients: 
                c.terminate()
            sys.exit()
            break

        elif head == 'insert' and request_size > 3:
            origin = int(request[1])
            key = request[2]
            value = ' '.join(request[3:])

            insert(origin, key, value)

        elif head == 'search' and request_size > 2:
            origin = int(request[1])
            key = request[2]

            search(origin, key)

        elif head == 'info' and request_size > 1:
            node_id = int(request[1])
            node = ring[node_id]
            print(node)

        else:
            print('Command not found')
            print_instructions()


if __name__ == "__main__":
    main()       