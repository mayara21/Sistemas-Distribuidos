class PeersLister:
    peers = []

    def remove_from_peers(self, name: str):
        if self.exists_in_peers(name):
            self.peers.remove(name)


    def add_to_peers(self, name: str):
        self.peers.append(name)

    def exists_in_peers(self, name: str) -> bool:
        exists: bool = False
        if self.peers.count(name) != 0:
            exists = True 
        
        return exists

    def is_empty(self) -> bool:
        empty = True
        if len(self.peers) != 0:
            empty = False

        return empty

    def get_peers(self):
        return_list = self.peers
        return return_list
        

peers_lister = PeersLister()