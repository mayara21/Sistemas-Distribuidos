import socket as sock
import threading

class PeerConnectionsLister:
    connections: dict = {}
    lock = threading.RLock()

    def add_connection(self, name, socket, thread, shutdown_event):
        self.lock.acquire()
        self.connections[name] = (socket, thread, shutdown_event)
        self.lock.release()

    def pop_connection_by_name(self, name):
        self.lock.acquire()
        socket, thread, event = self.connections.pop(name)
        self.lock.release()
        return (socket, thread, event)

    def pop_connection_by_socket(self, socket):
        self.lock.acquire()
        name = self.get_name_by_socket(socket)
        if name:
            self.connections.pop(name)
        self.lock.release()

        return (name, socket)

    def get_name_by_socket(self, socket):
        found_name = None
        self.lock.acquire()
        for name, (client_socket, thread, event) in self.connections.items():
            if client_socket == socket:
                found_name = name
        self.lock.release()

        return found_name

    def get_connection_by_name(self, name):
        self.lock.acquire()
        conn = self.connections[name]
        self.lock.release()
        return conn

    def get_all_connections(self):
        self.lock.acquire()
        conn = self.connections.values()
        self.lock.release()
        return conn


connections_lister = PeerConnectionsLister()