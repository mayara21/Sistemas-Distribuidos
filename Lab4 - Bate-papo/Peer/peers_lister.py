import threading

class PeersLister:
    peers = []
    lock = threading.RLock()

    def remove_from_peers(self, name: str):
        self.lock.acquire()
        if self.exists_in_peers(name):
            self.peers.remove(name)

        self.lock.release()

    def add_to_peers(self, name: str):
        self.lock.acquire()
        self.peers.append(name)
        self.lock.release()

    def exists_in_peers(self, name: str) -> bool:
        exists: bool = False
        self.lock.acquire()
        if self.peers.count(name) != 0:
            exists = True 
        self.lock.release()
        
        return exists

    def is_empty(self) -> bool:
        empty = True
        self.lock.acquire()
        if len(self.peers) != 0:
            empty = False
        self.lock.release()

        return empty

    def get_peers(self):
        self.lock.acquire()
        return_list = self.peers
        self.lock.release()
        return return_list
        

peers_lister = PeersLister()