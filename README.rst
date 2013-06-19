corrections
===========

An extendable Python based Twitter bot which will reply to various keyworded tweets.

*"Isn't this against the ToS?"*, I hear you ask. Well, sort of, but sort of not. Yes, it might be covered by the *spamming* or *unsolicited mentions* rules, but in my opinion, no more than some asshole going around correcting people manually, depending on your settings.

Example usage
-------------
Here's my favourite use of the Corrections bot (and why I actually wrote this): the **a lot** correction bot:

.. code-block:: python

    # -*- coding: utf-8 -*-
    from corrections import Correct
    from random import choice

    class Alot(Correct):
        auth = (OAUTH_TOKEN,
                OAUTH_SECRET,
                CONSUMER_KEY,
                CONSUMER_SECRET)
        phrases = ["alot"]
        force_fetch = True
        cooldown = (60 * 5, 60 * 3)

        def reply(self, phrase, user):
            return choice([
                "@{user}: a lot*",
                "@{user}: Surely you mean 'a lot', right?",
                "@{user}: I think you meant 'a lot'!",
                "@{user}: Come on, use 'a lot', lazy..",
                "@{user}: Alot is sad you can't use 'a lot' right..",
                "@{user}: There should be a space in there somewhere.. 'a lot'*",
            ]).format(user=user)

    if __name__ == "__main__":
        correct = Alot()
        correct()
