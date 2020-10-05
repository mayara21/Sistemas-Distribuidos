from user import User
import threading

class UserLister:

    user_list = []
    lock = threading.RLock()

    def add_to_list(self, user: User):
        self.lock.acquire()
        self.user_list.append(user)
        self.lock.release()

    def remove_from_list(self, name: str):
        self.lock.acquire()
        user = self.find_user_by_name(name)
        if user:
            self.user_list.remove(user)
        self.lock.release()
    
    def get_name_list(self):
        simplified_list = []
        self.lock.acquire()
        for user in self.user_list:
            simplified_list.append(user.name)
        self.lock.release()

        return simplified_list

    def find_user_by_name(self, name: str) -> User:
        found_user = None
        self.lock.acquire()
        for user in self.user_list:
            if user.name == name:
                found_user = user

        self.lock.release()
        return found_user


user_lister = UserLister()