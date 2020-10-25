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
        hash_key = hashlib.sha1(key.encode()).hexdigest()
        hash_key = int(hash_key, 16)
        mod_hash_key = hash_key % pow(2, self.quant)

        self.exposed_insert_hash(mod_hash_key, value)


    def exposed_insert_hash(self, hash_key, value):
        #print(self.id, self.finger)
        node_to_insert = None

        if hash_key == self.id:
            self.content[hash_key] = value

        elif hash_key == self.successor.id:
            node_to_insert = self.successor
        
        else:
            node_to_insert = self._closest_preceding_node(hash_key)
        
        if node_to_insert:
            connection = rpyc.connect(node_to_insert.address, node_to_insert.port)
            connection.root.exposed_insert_hash(hash_key, value)
            connection.close()


    def exposed_search_key(self, caller, key, search_id):
        hash_key = hashlib.sha1(key.encode()).hexdigest()
        hash_key = int(hash_key, 16)
        mod_hash_key = hash_key % pow(2, self.quant)
        
        self.exposed_search_hash(caller, mod_hash_key, search_id)


    def exposed_search_hash(self, caller, hash_key, search_id):
        #print(self.id, self.finger)
        node_to_search = None

        if hash_key == self.id:
            value = self.content[hash_key]
            caller(search_id, self.id, value)

        elif hash_key == self.successor.id:
            node_to_search = self.successor
        
        else:
            node_to_search = self._closest_preceding_node(hash_key)
        
        if node_to_search:
            connection = rpyc.connect(node_to_search.address, node_to_search.port)
            connection.root.exposed_search_hash(caller, hash_key, search_id)
            connection.close()

    def _closest_preceding_node(self, hash_key):
        for node in reversed(self.finger):
            if node.id <= hash_key:
                return node

        if hash_key < self.id:
            return self.finger[self.quant - 1]


    def __repr__(self):
        return 'Node ' + str(self.id) + ' with address ' + self.address + ' in port ' + str(self.port)