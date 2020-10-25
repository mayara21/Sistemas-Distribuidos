import socket as sock
import rpyc
from rpyc.utils.server import ThreadedServer 
import hashlib

class Node(rpyc.Service):
    id: int
    address: str
    port: int
    successor: "Node"
    finger = []
    content: dict = {}
    quant: int
    
    def __init__(self, id, address, port):
        self.id = id
        self.address = address
        self.port = port

    def set_successor(self, successor):
        self.successor = successor

    def set_finger_table(self, finger):
        self.finger = finger
        self.quant = len(finger)

    def start(self):
        client = ThreadedServer(self, port=self.port)
        client.start()


    def exposed_insert_key(self, key, value):
        hash_key = hashlib.sha1(key.encode()).hexdigest
        hash_key = int(hash_key, 16)

        mod_hash_key = hash_key % pow(2, self.quant)
        print('hash: ', mod_hash_key)
        node_to_insert = None

        if mod_hash_key == self.id:
            print('inseri no: ', self.id)
            self.content[mod_hash_key] = value
        
        elif mod_hash_key <= self.successor.id:
            node_to_insert = self.successor

        else:
            print(self.finger)
            for node in reversed(self.finger):
                if mod_hash_key >= node.id:
                    node_to_insert = node
                    break

        if node_to_insert:
            connection = rpyc.connect(node_to_insert.address, node_to_insert.port)
            connection.root.exposed_insert_hash(mod_hash_key, value)
            connection.close()


    def exposed_insert_hash(self, hash_key, value):
        if hash_key == self.id:
            print('inseri no: ', self.id)
            self.content[hash_key] = value
        
        else:
            print(self.finger)
            for node in reversed(self.finger):
                if hash_key <= node.id:
                    connection = rpyc.connect(node.address, node.port)
                    connection.root.exposed_insert_hash(hash_key, value)
                    connection.close()
                    break


    def exposed_search_key(self, caller, key, search_id):
        hash_key = hashlib.sha1(key.encode()).hexdigest
        hash_key = int(hash_key, 16)
        mod_hash_key = hash_key % pow(2, self.quant)

        if mod_hash_key == self.id:

    #def find_successor(id: int):