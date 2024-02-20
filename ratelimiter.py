#naive ratelimiter
from time import time

class ratelimit():
    def __init__(self, min_delay):
        self.delay = min_delay
        self.last_action = 0
        self.action_queue = []
    def action(self, manual, target, args):
        print("action~", target, args)
        if time() - self.last_action > self.delay:
            self.last_action = time()
            target(*args)
            try: self.action_queue.remove((target, args))
            except: print("did not remove", target, args)
        else:
            print("deferred")
            if manual:
                self.action_queue.append((target, args))
    def lazyrun(self):
        if len(self.action_queue) <= 0: return
        f = self.action_queue[0][0]
        args = self.action_queue[0][1]
        self.action(False, f, args)
