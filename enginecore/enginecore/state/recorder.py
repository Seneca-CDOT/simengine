
"""Record/Replay functionalities"""

import functools
from itertools import zip_longest
from datetime import datetime as dt
import time


class Recorder:

    def __init__(self):
        self._actions = []


    def __call__(self, work):
        @functools.wraps(work)
        def record_wrapper(asset_self, *f_args, **f_kwargs):
            self._actions.append({
                'work': functools.partial(work, asset_self, *f_args, **f_kwargs),
                'timestamp': dt.now()
            })
            return work(asset_self, *f_args, **f_kwargs)
        return record_wrapper


    def replay_all(self):
        """Replay all actions"""
        self.replay_range(slice(None, None))


    def replay_range(self, slc):
        """Replay a range of actions"""

        for action, next_action in zip_longest(self._actions[slc], self._actions[1:][slc]):

            action['work']()
            if next_action:
                time.sleep((next_action['timestamp'] - action['timestamp']).seconds)
