import socket as sock

class PeerConnectionsLister:
    connections: dict = {}

    def add_connection(self, name, socket):
        self.connections[name] = socket

    def pop_connection_by_name(self, name):
        socket = self.connections.pop(name)
        return socket

    def pop_connection_by_socket(self, socket):
        name = self.get_name_by_socket(socket)
        if name:
            self.connections.pop(name)

        return (name, socket)

    def get_name_by_socket(self, socket):
        found_name = None
        for name, client_socket in self.connections.items():
            if client_socket == socket:
                found_name = name

        return found_name

    def get_connection_by_name(self, name):
        conn = self.connections[name]
        return conn

    def get_all_connections(self):
        conn = self.connections.values()
        return conn

    def contains(self, socket):
        name = self.get_name_by_socket(socket)
        if name:
            return True
        else:
            return False


connections_lister = PeerConnectionsLister()