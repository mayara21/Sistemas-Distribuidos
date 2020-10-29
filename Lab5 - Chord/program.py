import socket as sock
import sys
import select
import multiprocessing
import rpyc
import random
from node import Node
from rpyc.utils.server import ThreadedServer 

class Program(rpyc.Service):

    HOST: str = 'localhost'
    PORT: int = 6000

    ring = []
    clients = []

    # initialize a process to run each node
    def start(self):
        for node in self.ring:
            client = multiprocessing.Process(target=node.start)
            client.start()
            self.clients.append(client)


    # creates Chord Ring
    def create_ring(self, quant):
        ring_size = pow(2, quant)
        ports = []

        # creates each node, adding to the ring
        for id in range (ring_size):
            port = random.randint(7000, 15000) # generates a random port, checking for repetitions
            while port in ports:
                port = random.randint(7000, 15000)
            
            ports.append(port)
            self.ring.append(Node(id, 'localhost', port))

        # adds successor and finger table for each node
        for id in range (ring_size):
            node: Node = self.ring[id]
            successor: Node = self.ring[id + 1] if (id + 1 < ring_size) else self.ring[0]
            node.set_successor(successor)

            finger = []
            for k in range (1, quant + 1):
                value: int = (id + pow(2, k - 1)) % ring_size
                finger.append(self.ring[value])

            node.set_finger_table(finger)

        self.start()

    # method to get node info (to be called remotely)
    def exposed_get_node(self, node_id):
        try:
            node = self.ring[node_id]
            return (node.address, node.port)

        except IndexError:
            return None


    # alternate method that returns all the nodes at once
    def exposed_nodes(self):
        nodes = []
        for node in self.ring:
            nodes.append((node.address, node.port))

        return nodes


    def main(self):
        quant = input('Insert N: ') # receives the desired N to create 2ˆn nodes
        self.create_ring(int(quant))
        print('Ring created!')

        # initialize the main program to receive RPC calls
        srv = ThreadedServer(self, port = self.PORT)
        srv.start()


if __name__ == "__main__":
    prog = Program()
    prog.main()
