"""Record/Replay functionalities"""

import functools
from itertools import zip_longest
from datetime import datetime as dt
import time
import logging

from pprint import pprint as pp


class Recorder:
    def __init__(self):
        self._actions = []
        self._enabled = True

    def __call__(self, work):
        @functools.wraps(work)
        def record_wrapper(asset_self, *f_args, **f_kwargs):

            if (
                asset_self.__module__.startswith("enginecore.state.api")
                and self._enabled
            ):
                partial_func = functools.partial(work, asset_self, *f_args, **f_kwargs)
                self._actions.append(
                    {
                        "work": functools.update_wrapper(partial_func, work),
                        "timestamp": dt.now(),
                    }
                )
            return work(asset_self, *f_args, **f_kwargs)

        return record_wrapper

    def list_all(self):
        pp(self._actions)

    def erase_all(self):
        self.erase_range(slice(None, None))

    def erase_range(self, slc):
        del self._actions[slc]

    def replay_all(self):
        """Replay all actions"""
        self.replay_range(slice(None, None))

    def replay_range(self, slc):
        """Replay a range of actions"""

        self._enabled = False

        for action, next_action in zip_longest(
            self._actions[slc], self._actions[1:][slc]
        ):

            action_info = "Replaying: [ {action}{args} ]".format(
                action=action["work"].__name__, args=action["work"].args
            )

            logging.info(action_info)
            action["work"]()

            if next_action:
                next_delay = (next_action["timestamp"] - action["timestamp"]).seconds
                logging.info("Paused for %s seconds...", next_delay)
                time.sleep(next_delay)

        self._enabled = True


RECORDER = Recorder()
