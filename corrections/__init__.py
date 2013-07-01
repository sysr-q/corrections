# -*- coding: utf-8 -*-
import gevent.monkey
gevent.monkey.patch_all()

import gevent
from gevent.queue import Queue
import twitter
from threading import Thread
import time
import re


# change here, change in setup.py
__version__ = "0.2.3"

class CorrectionsException(Exception):
    pass


class Correct(object):
    """ Is it a bird? Is it a plane? No, it's the Corrections twitter bot.
        How irritating.

        auth - a tuple/list with the information from the Twitter dev site:
            (OAUTH_TOKEN, OAUTH_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
        phrases - an iterable (or string) of phrases to search for
        cooldown - how long to wait (in seconds) between searching for new
            tweets and sending off tweets, as a tuple. e.g. (60, 30)
        force_fetch - should we fetch new tweets, even if we haven't
            exhausted our current tweet queue?
        max_queue - how many tweets should we store in our queue before
            we just stop caring?
        reply_to_rt - should we bother replying to retweets? Sometimes
            this is useless, sometimes it's alright. Take your pick.
        ignore_display_names - should we correct people that have the
            type in their @display_name?
        dry - do everything but don't actually send the tweets

    """
    auth = None
    phrases = None
    cooldown = (60, 60 * 3)  # 1 min / 3 min respectively
    force_fetch = False
    max_queue = 250
    reply_to_rt = False
    ignore_display_names = True
    dry = False

    def __init__(self):
        if self.auth is None:
            raise CorrectionsException("No auth given.")
        self.t = twitter.Twitter(auth=twitter.OAuth(*self.auth))
        try:
            # List, tuple, etc.
            iterator = iter(self.phrases)
        except TypeError:
            # String, int, whatever.
            self.phrases = [self.phrases]
        # We're going to want strings anyway, so..
        self.phrases = [str(p) for p in self.phrases]
        self._cooldown_fetch, self._cooldown_tweet = self.cooldown

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

    def _is_display_name(self, tweet):
        for p in self.phrases:
            if re.findall(r'@[^\s]*{0}[^\s]*'.format(p), flags=re.I):
                return True
        return False

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
            if not self.ignore_display_names and self._is_display_name(t):
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

    def take_action(self, tweet, username, tid):
        reply = self.reply(tweet, username)
        if not self.dry:
            self.t.statuses.update(status=reply, in_reply_to_status_id=tid)

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
            self.take_action(task['text'], task['user']['screen_name'], task['id'])
            self._next_tweet = time.time() + self._cooldown_tweet
    __call__ = do_loop

    def kill(self):
        # Good enough? Sure.
        self.producer.kill()

    def reply(self, phrase, user):
        """ Override this!
        """
        return "IDK my BFF Jill?"
