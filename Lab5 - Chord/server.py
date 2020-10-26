import socket as sock
import sys
import select
import multiprocessing
import rpyc
from node import Node
from rpyc.utils.server import ThreadedServer 

class Server(rpyc.Service):

    HOST: str = 'localhost'
    PORT: int = 5000

    ring = []
    clients = []

    def start(self):
        for node in self.ring:
            client = multiprocessing.Process(target=node.start)
            client.start()
            self.clients.append(client)


    def create_ring(self, quant):
        ring_size = pow(2, quant)

        for id in range (ring_size):
            self.ring.append(Node(id, 'localhost', self.PORT + id + 1))

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


    def exposed_get_node(self, node_id):
        try:
            node = self.ring[node_id]
            return (node.address, node.port)

        except IndexError:
            return None


    def exposed_nodes(self):
        nodes = []
        for node in self.ring:
            nodes.append((node.address, node.port))

        return nodes


    def main(self):
        quant = input('Insert N: ')
        self.create_ring(int(quant))
        print('Ring created!')

        srv = ThreadedServer(self, port = self.PORT)
        srv.start()


if __name__ == "__main__":
    srv = Server()
    srv.main()
