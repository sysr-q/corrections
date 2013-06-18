# -*- coding: utf-8 -*-
import gevent.monkey
gevent.monkey.patch_all()
import gevent
from gevent.queue import Queue
import twitter
from threading import Thread

# debuggerin
import requests
__version__ = "0.1.0"


class Correct(object):
    def __init__(self, auth, phrases=None):
        """ Create a new correctional bot, with a Twitter instance ready.

            :auth: a tuple/list with the information from Twitter:
                (OAUTH_TOKEN, OUTH_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
            :phrases: an iterable (or string) of phrases to search for.
        """
        if auth is not None:
            self.t = twitter.Twitter(auth=twitter.OAuth(*auth))
        else:
            self.t = None
        try:
            # List, tuple, etc.
            iterator = iter(phrases)
        except TypeError:
            # String, int, whatever.
            self.phrases = [phrases]
        else:
            # Whoo, iterable!
            self.phrases = phrases
        self.queue = Queue()
        self.producer = gevent.spawn(self._produce)

    def _add_work(self, amt=50):
        [self.queue.put_nowait(i) for i in xrange(amt)]

    def _produce(self):
        while True:
            if not self.queue.empty():
                print "Not empty!", self.queue.qsize()
                gevent.sleep(1)
                continue
            self._add_work(10)
            gevent.sleep(0)

    def do_loop(self):
        while True:
            if self.queue.empty():
                print "Lel empty!!"
                gevent.sleep(0)
            task = self.queue.get()
            r = requests.get('http://httpbin.org/get', params={"task": task})
            print r.json()
    __call__ = do_loop

    def reply(self, phrase, user):
        return "IDK my BFF Jill?"
