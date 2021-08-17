"""Record/Replay functionalities"""

import functools
from itertools import zip_longest
from datetime import datetime as dt
import time
import logging
import inspect
import pickle
import json
import codecs

logger = logging.getLogger(__name__)


class Recorder:
    """Recorder can be used to record and replay methods or functions"""

    def __init__(self, module: str):
        self._actions = []
        self._enabled = True
        self._replaying = False
        self._module = module

    def __call__(self, work: callable):
        """Make an instance of recorder a callable object that
        can be used as a decorator with functions/class methods.

        Function calls will be registered by the recorder & can be replayed later on.

        Example:
            recorder = Recorder()
            @recorder
            def my_action(self):
                ...

            each call to my_action() will be stored in action
            history of the recorder instance,

            *Note* that class or instance implementing recorded action
            must have key attribute
        """

        @functools.wraps(work)
        def record_wrapper(asset_self, *f_args, **f_kwargs):

            if asset_self.__module__.startswith(self._module) and self._enabled:

                func_args = tuple((work, asset_self))

                partial_func = functools.partial(*func_args, *f_args, **f_kwargs)
                self._actions.append(
                    {
                        "work": functools.update_wrapper(partial_func, work),
                        "time": dt.now(),
                    }
                )
            return work(asset_self, *f_args, **f_kwargs)

        return record_wrapper

    @property
    def enabled(self) -> bool:
        """Recorder status indicating if it's accepting & recording new actions"""
        return self._enabled

    @property
    def replaying(self) -> bool:
        """Recorder status indicating if recorder is in process of replaying actions"""
        return self._replaying

    @enabled.setter
    def enabled(self, value: bool):
        if not self.replaying:
            self._enabled = value

    def save_actions(
        self,
        action_file: str = "/tmp/recorder_action_file.json",
        slc: slice = slice(None, None),
    ):
        """Save actions into a json file (actions can be later loaded)
        Args:
            action_file(optional): action history will be saved in this file
            slc(optional): range of actions to be saved,
                           defaults to all if not specified
        Example:
            Action history is saved in the following format:
            [
                // for instance methods:
                {
                    "type": "ClassName",
                    "key": integer key,
                    "args": "..encoded base64 bytes..",
                    "kwargs": "..encoded base64 bytes..",
                    "work": "method_name",
                    "timestamp": "utc-timestamp"
                },
                // for class methods:
                {
                    "type": "..encoded base64 bytes..",
                    "args": "..encoded base64 bytes..",
                    "kwargs": "..encoded base64 bytes..",
                    "work": "method_name",
                    "timestamp": "utc-timestamp"
                },
                {...}
            ]
            Where "..encoded base64 bytes.." is codecs base64
            encoded pickled python object
        """
        serialized_actions = []
        json_pickle = lambda x: codecs.encode(pickle.dumps(x), "base64").decode()

        for action in self._actions[slc]:

            action_info = {
                "args": json_pickle(action["work"].args[1:]),
                "kwargs": json_pickle(action["work"].keywords),
                "work": action["work"].__wrapped__.__name__,
                "timestamp": action["time"].timestamp(),
            }

            if hasattr(action["work"].args[0], "key"):
                action_info["key"] = action["work"].args[0].key
                action_info["type"] = action["work"].args[0].__class__.__name__
            else:
                action_info["type"] = json_pickle(action["work"].args[0])

            serialized_actions.append(action_info)

        with open(action_file, "w") as action_f_handler:
            json.dump(serialized_actions, action_f_handler, indent=2)

    def load_actions(
        self,
        map_key_to_state: callable,
        action_file: str = "/tmp/recorder_action_file.json",
        slc=slice(None, None),
    ):
        """load action history from a file;
        Note that this function clears existing actions

        Args:
            map_key_to_state: instances are not serialized instead their keys
                              are stored in the file; the de-serialization is key-based
                              and must be provided with this argument
                              by mapping keys to python objects
            action_file(optional): action history will be saved in this file
            slc(optional): range of actions to be loaded from a file,
                           defaults to all if not specified
        """

        if self._replaying:
            logger.warning("Cannot load actions while replaying")
            return

        json_unpickle = lambda x: pickle.loads(codecs.decode(x.encode(), "base64"))
        self._actions = []

        with open(action_file, "r") as action_f_handler:
            serialized_actions = json.load(action_f_handler)

        for action in serialized_actions[slc]:
            if "key" in action:
                state = map_key_to_state(action["key"])
            else:
                state = json_unpickle(action["type"])

            args = json_unpickle(action["args"])
            kwargs = json_unpickle(action["kwargs"])
            action_time = dt.fromtimestamp(action["timestamp"])

            work = getattr(state, action["work"]).__wrapped__
            partial_func = functools.partial(work, state, *args, **kwargs)

            self._actions.append(
                {
                    "work": functools.update_wrapper(partial_func, work),
                    "time": action_time,
                }
            )

    def get_action_details(self, slc: slice = slice(None, None)) -> list:
        """Human-readable details on action history;
        Note that this method "serializes" actions
        so they are not callable when returned.

        Args:
            slc(slice): range of actions to be returned
        Returns:
            list containing history of actions
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
                    "timestamp": int(action["time"].timestamp()),
                    "number": self._actions.index(action),
                }
            )

        return action_details

    def erase_all(self):
        """Clear all actions"""
        self.erase_range(slice(None, None))

    def erase_range(self, slc: slice = slice(None, None)):
        """Delete a slice of actions
        Args:
            slc(slice): range of actions to be deleted
        """
        del self._actions[slc]

    def replay_all(self):
        """Replay all actions"""
        self.replay_range(slice(None, None))

    def replay_range(self, slc: slice = slice(None, None)):
        """Replay a slice of actions
        Args:
            slc: range of actions to be performed
        """

        pre_replay_enabled_status = self.enabled
        self.enabled = False
        self._replaying = True

        for action, next_action in self.actions_iter(self._actions, slc):

            action_info = "Replaying: [ {action}{args} ]".format(
                action=action["work"].__name__, args=action["work"].args
            )

            # perform action
            action["work"]()

            # simulate pause between 2 actions
            if next_action:
                next_delay = (next_action["time"] - action["time"]).seconds
                logger.info("Paused for %s seconds...", next_delay)
                time.sleep(next_delay)

        self._replaying = False
        self.enabled = pre_replay_enabled_status

    @classmethod
    def actions_iter(cls, actions: list, slc: slice = slice(None, None)) -> zip_longest:
        """Get an iterator yielding current & next actions
        Args:
            actions(list): action history
            slc(slice): range of actions
        Returns:
            iterator aggragating actions & actions+1 in one iter
        """
        return zip_longest(actions[slc], actions[slc][1:])

    @classmethod
    def perform_dry_run(cls, actions: list, slc: slice = slice(None, None)):
        """Perform replay dry run by outputting step-by-step actions
        (without executing them)

        Args:
            actions(list): action history, must contain action "number",
                           "work" (action itself) & "timestamp"
            slc(slice): range of actions
        """

        for action, next_action in cls.actions_iter(actions, slc):

            print("{number}) [executing]: {work}".format(**action))
            out_pad = len("{number}) ".format(**action)) * " "

            if next_action:
                next_delay = (
                    dt.fromtimestamp(next_action["timestamp"])
                    - dt.fromtimestamp(action["timestamp"])
                ).seconds

                print(
                    "{pad}[sleeping]:  {sleep} seconds".format(
                        pad=out_pad, sleep=next_delay
                    )
                )

                for _ in range(1, next_delay + 1):
                    print("{pad}.".format(pad=out_pad))
                    time.sleep(1)


RECORDER = Recorder(module="enginecore.state.api")
