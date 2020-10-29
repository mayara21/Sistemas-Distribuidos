import socket as sock
import rpyc
import sys
import copy
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

    # initialize RPC server for node, to receice remote calls
    def start(self):
        client = ThreadedServer(self, port=self.port)
        client.start()

    # method to be called when you are the origin node, to insert a key
    def exposed_insert_key(self, key, value):
        hash_key = hashlib.sha1(key.encode()).hexdigest() # generate a hash
        hash_key = int(hash_key, 16)
        self.exposed_insert_hash(hash_key, value)

    # method to insert a hash in the ring
    def exposed_insert_hash(self, hash_key, value):
        #print(self.id, self.finger)
        node_to_insert = None
        mod_hash_key = hash_key % pow(2, self.quant)

        # find where the key should be inserted
        if mod_hash_key == self.id: # compare if it's equal because the nodes are consecutive
            #print('inseriu ' + str(hash_key) + ' em ' + str(self.id))
            self.content[hash_key] = value # insert key-value pair in node

        elif mod_hash_key == self.successor.id:
            node_to_insert = self.successor
        
        else:
            node_to_insert = self._closest_preceding_node(mod_hash_key)
        
        if node_to_insert:
            try:
                connection = rpyc.connect(node_to_insert.address, node_to_insert.port)
                connection.root.exposed_insert_hash(hash_key, value) # call insert hash from the following node
                connection.close()
            except (ConnectionRefusedError, ConnectionResetError, ConnectionError, ConnectionAbortedError):
                print('There was a problem connecting to the node, try later')
                return

    # method to be called when you are the origin node, to find a key
    def exposed_search_key(self, caller, key, search_id):
        hash_key = hashlib.sha1(key.encode()).hexdigest()
        hash_key = int(hash_key, 16)
        
        self.exposed_search_hash(caller, hash_key, search_id)

    # method to search a hash in the ring (same logic as insert)
    def exposed_search_hash(self, caller, hash_key, search_id):
        #print(self.id, self.finger)
        node_to_search = None
        mod_hash_key = hash_key % pow(2, self.quant)

        if mod_hash_key == self.id:
            try:
                value = self.content[hash_key]
                caller(search_id, self.id, value) # calls the method returning the value to the caller (client)
            
            except KeyError:
                message = 'The key was not found'
                caller(search_id, None, message)

        elif mod_hash_key == self.successor.id:
            node_to_search = self.successor
        
        else:
            node_to_search = self._closest_preceding_node(mod_hash_key)
        
        if node_to_search:
            try:
                connection = rpyc.connect(node_to_search.address, node_to_search.port)
                connection.root.exposed_search_hash(caller, hash_key, search_id)
                connection.close()
                
            except (ConnectionRefusedError, ConnectionResetError, ConnectionError, ConnectionAbortedError):
                message = 'There was a problem connecting to the node, try later'
                caller(search_id, None, message)                


    # find the closest node that precedes the key
    def _closest_preceding_node(self, hash_key):
        h = hash_key

        if hash_key < self.id:
            h += pow(2, self.quant)
        
        for node in reversed(self.finger):
            node_id = node.id if node.id > self.id else node.id + pow(2, self.quant)
            if node_id <= h:
                return node


    # redefines how the node is printed
    def __repr__(self):
        return 'Node ' + str(self.id) + ' with address ' + self.address + ' in port ' + str(self.port)