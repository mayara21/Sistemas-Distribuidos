import socket as sock
import threading

class ConnectionsLister:

    connections: dict = {}
    lock = threading.RLock()

    def add_connection(self, name, socket):
        self.lock.acquire()
        self.connections[name] = socket  
        self.lock.release() 


    def get_connection_by_name(self, name) -> sock.socket: #try catch?
        self.lock.acquire()
        try:
            return self.connections[name]
        except KeyError:
            return None
        finally:
            self.lock.release()


    def pop_connection_by_name(self, name) -> sock.socket:
        self.lock.acquire()
        try:
            return self.connections.pop(name)
        except KeyError:
            return None
        finally:
            self.lock.release()


    def pop_connection_by_socket(self, socket) -> (str, sock.socket):
        self.lock.acquire()
        name = self.get_name_by_socket(socket)
        conn = self.pop_connection_by_name(name)
        self.lock.release()
        return (name, conn)


    def get_name_by_socket(self, socket) -> str:
        name = None
        self.lock.acquire()
        for user_name, client_socket in self.connections.items():
            if client_socket == socket:
                name = user_name
                
        self.lock.release()
        return name

connections_lister = ConnectionsLister()