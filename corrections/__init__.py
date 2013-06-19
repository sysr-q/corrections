# -*- coding: utf-8 -*-
import gevent.monkey
gevent.monkey.patch_all()

import gevent
from gevent.queue import Queue
import twitter
from threading import Thread
import time


# change here, change in setup.py
__version__ = "0.1.0"


class Correct(object):
    def __init__(self,
                 auth,
                 phrases=None,
                 cooldown=(30, 10),
                 force_fetch=False,
                 max_queue=250,
                 reply_to_rt=False):
        """ Create a new correctional bot, with a Twitter instance ready.

            :auth: a tuple/list with the information from Twitter:
                (OAUTH_TOKEN, OUTH_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
            :phrases: an iterable (or string) of phrases to search for.
            :cooldown: how long to wait in seconds between searching for
                new tweets, and sending off tweets; as a tuple, like (20, 30)
            :force_fetch: should we fetch new tweets, even if we haven't
                fully drained our tweet queue?
            :max_queue: when should we stop caring about new tweets?
            :reply_to_rt: should we bother replying to retweets? Sometimes
                this is useless, sometimes it's alright. Take your pick.
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
        self.max_queue = max_queue
        self.reply_to_rt = reply_to_rt

        self.queue = Queue()
        self.producer = None
        self.seen = []
        self._next_fetch = time.time()
        self._next_tweet = time.time()
        self.account_settings = self.t.account.settings()
        self.display_name = self.account_settings['screen_name']

    def _in_reply_to_us(self, tweet):
        if 'in_reply_to_screen_name' not in tweet:
            return False
        if tweet['in_reply_to_screen_name'] is None:
            return False
        if tweet['in_reply_to_screen_name'] != self.display_name:
            return False
        # Who knows, probably us.
        return True

    def _from_us(self, tweet):
        return tweet['user']['screen_name'] == self.display_name

    def _is_retweet(self, tweet):
        """ If we get back False, it's OK to reply to;
            True means don't reply, it's a trap.
        """
        if self.reply_to_rt:
            return False
        return 'retweeted_status' in tweet

    def _fetch_tweets(self):
        tweets = self.t.search.tweets(q=" OR ".join(self.phrases), lang="en")
        for t in tweets['statuses']:
            if self.queue.qsize() >= self.max_queue:
                break
            # Why single rather than stacked? It's cleaner.
            if self._in_reply_to_us(t):
                continue
            if self._from_us(t):
                continue
            if self._is_retweet(t):
                continue
            if t['id'] in self.seen:
                continue

            self.seen.append(t['id'])
            self.queue.put_nowait(t)
        self._next_fetch = time.time() + self._cooldown_fetch

    def _produce(self):
        while True:
            if not self.force_fetch and not self.queue.empty():
                gevent.sleep(0)
                continue
            if self.queue.qsize() >= self.max_queue:
                gevent.sleep(0)
                continue
            if self._next_fetch > time.time():
                gevent.sleep(0)
                continue
            self._fetch_tweets()
            gevent.sleep(0)

    def do_loop(self):
        # Actually start our produce loop.
        self.producer = gevent.spawn(self._produce)
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

    def kill(self):
        # Good enough? Sure.
        self.producer.kill()

    def reply(self, phrase, user):
        """ Override this!
        """
        return "IDK my BFF Jill?"
