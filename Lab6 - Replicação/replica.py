import socket as sock

class Replica:
    ip: str = 'localhost'
    id: int
    base_port: int = 6000
    port: int
    primary_copy_id: int
    value: int
    local_changes: int
    replicas = []
    history = []

    def __init__(self, id):
        self.id = id
        self.port = self.base_port + id
        self.primary_copy_id = 1
        self.local_changes = 0


    def commit(self):
        if (self.local_changes == 0):
            return 'No local changes to commit'
        else:
            # send new value to all replicas
            return str(self.local_changes) + ' changes successfully commited'


    def update_primary_copy(self, primary_copy_id):
        self.primary_copy_id = primary_copy_id
    

    def change_value(self, new_value):
        if self.primary_copy_id == self.id:
            self.local_changes += 1
            self._update_value(self.id, new_value)

        else:
            print('temp')
            # ask primary_copy_id for the hat


    def _update_value(self, origin_replica, new_value):
        self.value = new_value
        self.history.append((origin_replica, new_value))


    def _notify_primary_copy(self):
        print('temp')
        # send message to all replicas announcing you have the hat



def main():
    id = 1
    replica = Replica(id)
    
    while(True):
        command = input()
        request = command.split(' ')
        head = request[0]

        if head == '/read':
            print(replica.value)

        elif head == '/history':
            history = replica.history
            if not history:
                print('There were no alterations in the value so far')
            else:
                print(history)

        elif head == '/update' and len(request) > 1:
            value = request[1]

            if isinstance(value, int):
                replica.change_value(value)
            else:
                print('The value needs to be an integer')

        elif head == '/commit':
            message = replica.commit()
            print(message)

        elif head == 'close':
            break

        else:
            print('Command not found')