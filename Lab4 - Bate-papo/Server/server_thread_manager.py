import threading

class ServerThreadManager:

    threads = []

    def create_thread(self, function, params):
        thread = threading.Thread(target=function, args=params)
        self.threads.append(thread)

        return thread

    def join_threads(self):
        for thread in self.threads:
            thread.join()
