import socket as sock
import sys
import select
import multiprocessing
import rpyc
from node import Node

SERVER_HOST: str = 'localhost'
SERVER_PORT: int = 5000

nodes = []

search_id_counter = 0

def insert(originNode, key, value):
    try:
        node = nodes[originNode]
    
    except IndexError:
        node = get_node_info(originNode)
        if not node:
            return
    
    connection = rpyc.connect(node[0], node[1])
    connection.root.exposed_insert_key(key, value)
    connection.close()


def print_search_result(search_id_counter, found_node_id, result):
    print('Search ' + str(search_id_counter) + ' found the value "' + str(result) + '" in node ' + str(found_node_id))


def search(originNode, key):
    global search_id_counter
    try:
        node = nodes[originNode]
    
    except IndexError:
        node = get_node_info(originNode)
        if not node:
            return

    connection = rpyc.connect(node[0], node[1])
    connection.root.exposed_search_key(print_search_result, key, search_id_counter)
    connection.close()

    search_id_counter += 1


def get_node_info(node_id):
    conn = rpyc.connect(SERVER_HOST, SERVER_PORT)
    node = conn.root.exposed_get_node(node_id)
    conn.close()
    
    if not node:
        print('This node does not exist in the ring')
        return None
    
    nodes.append(node)
    return node


# def get_ring_info():
#     global nodes
#     conn = rpyc.connect(SERVER_HOST, SERVER_PORT)
#     nodes = list(conn.root.exposed_nodes())
#     conn.close()


def print_instructions():
    print('To insert a key-value pair, type: ')
    print('insert origin_node_id key value')
    print('To search a key, type: ')
    print('search origin_node_id key')
    print('To get info about a node: ')
    print('info node_id')

def main():

    print_instructions()

    while True:
        command = input()
        request = command.split(' ')
        head = request[0]
        request_size = len(request)

        # if command == 'close':
        #     for c in clients: 
        #         c.terminate()
        #     sys.exit()
        #     break

        if head == 'insert' and request_size > 3:
            origin = int(request[1])
            key = request[2]
            value = ' '.join(request[3:])

            insert(origin, key, value)

        elif head == 'search' and request_size > 2:
            origin = int(request[1])
            key = request[2]

            search(origin, key)

        else:
            print('Command not found')
            print_instructions()


if __name__ == "__main__":
    main()       