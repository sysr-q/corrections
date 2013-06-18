# -*- coding: utf-8 -*-
import gevent.monkey
gevent.monkey.patch_all()

import gevent
from gevent.queue import Queue
import twitter
from threading import Thread
import time

# debuggerin
import requests

# change here, change in setup.py
__version__ = "0.1.0"


class Correct(object):
    def __init__(self,
                 auth,
                 phrases=None,
                 cooldown=(30, 10),
                 force_fetch=False):
        """ Create a new correctional bot, with a Twitter instance ready.

            :auth: a tuple/list with the information from Twitter:
                (OAUTH_TOKEN, OUTH_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
            :phrases: an iterable (or string) of phrases to search for.
            :cooldown: how long to wait in seconds between searching for
                new tweets, and sending off tweets; as a tuple, like (20, 30)
            :force_fetch: should we fetch new tweets, even if we haven't
                fully drained our tweet queue?
        """
        self.t = twitter.Twitter(auth=twitter.OAuth(*auth))
        try:
            # List, tuple, etc.
            iterator = iter(phrases)
        except TypeError:
            # String, int, whatever.
            self.phrases = [phrases]
        else:
            # Whoo, iterable!
            self.phrases = phrases
        # We're going to want strings anyway, so..
        self.phrases = map(str, self.phrases)
        self._cooldown_fetch, self._cooldown_tweet = cooldown
        self.force_fetch = force_fetch

        self.queue = Queue()
        self.producer = gevent.spawn(self._produce)
        self.seen = []
        self._next_fetch = time.time()
        self._next_tweet = time.time()

    #def _add_work(self, amt=50):
    #    [self.queue.put_nowait(i) for i in xrange(amt)]

    def _fetch_tweets(self):
        tweets = self.t.search.tweets(q=" OR ".join(self.phrases), lang="en")
        for t in tweets['statuses']:
            if t['id'] in self.seen:
                continue
            self.seen.append(t['id'])
            print "Got:", t['id']   # /debug
            self.queue.put_nowait(t)
        self._next_fetch = time.time() + self._cooldown_fetch

    def _produce(self):
        while True:
            if not self.force_fetch and not self.queue.empty():
                gevent.sleep(0)
                continue
            if self._next_fetch > time.time():
                gevent.sleep(0)
                continue
            self._fetch_tweets()
            gevent.sleep(0)

    def do_loop(self):
        while True:
            if self.queue.empty():
                gevent.sleep(0)
            if self._next_tweet > time.time():
                gevent.sleep(0)
                continue
            task = self.queue.get()
            print u"Should be replying to: {0} (from @{1})".format(
                task['text'],
                task['user']['screen_name']
            )  # /debug
            self._next_tweet = time.time() + self._cooldown_tweet
    __call__ = do_loop

    def reply(self, phrase, user):
        return "IDK my BFF Jill?"
