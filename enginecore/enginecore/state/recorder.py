"""Record/Replay functionalities"""

import functools
from itertools import zip_longest
from datetime import datetime as dt
import time
import logging
import inspect


class Recorder:
    """Recorder can be used to record and replay methods belonging to a class
    Example:
        
    """

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

    def get_action_details(self, slc=slice(None, None)):
        """Human-readable details on action history
        Args:
            slc(slice): range of actions to be returned
        Returns:
            list: history of actions
        """
        action_details = []

        for action in self._actions[slc]:

            wrk_asset = action["work"].args[0]
            if inspect.isclass(wrk_asset):
                obj_str = wrk_asset.__name__
            else:
                obj_str = "{asset}({key})".format(
                    asset=type(wrk_asset).__name__, key=wrk_asset.key
                )

            action_details.append(
                {
                    "work": "{obj}.{func}{args}".format(
                        obj=(obj_str),
                        func=action["work"].__name__,
                        args=action["work"].args[1:],
                    ),
                    "timestamp": action["timestamp"],
                    "number": self._actions.index(action),
                }
            )

        return action_details

    def erase_all(self):
        """Clear all actions"""
        self.erase_range(slice(None, None))

    def erase_range(self, slc):
        """Delete a slice of actions
        Args:
            slc(slice): range of actions to be deleted
        """
        del self._actions[slc]

    def replay_all(self):
        """Replay all actions"""
        self.replay_range(slice(None, None))

    def replay_range(self, slc):
        """Replay a slice of actions
        Args:
            slc(slice): range of actions to be performed
        """
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
