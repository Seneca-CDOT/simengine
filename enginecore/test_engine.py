#!/usr/bin/python3
import os

from circuits import Component, handler
from enginecore.state.new_engine import Engine
from enginecore.state.api.state import IStateManager

import time
from queue import Queue

os.environ["SIMENGINE_WORKPLACE_TEMP"] = "simengine-test"

engine = Engine()
engine.start()


class VoltCompletionTracker(Component):
    channel = "volt-tracker"
    queue = Queue()

    @handler("AllVoltageBranchesDone")
    def pabam_volt(self, event, *args, **kwargs):
        print("\n\n---------> pabam volt!")

    @handler("AllLoadBranchesDone")
    def pabam_load(self, event, *args, **kwargs):
        print("\n\n---------> pabam load!")
        VoltCompletionTracker.queue.put("passed")


def _finish_test(test):
    print("\n" * 2)
    print("\n\n[TEST] finished {} \n\n".format(test))
    print("\n" * 2)


while True:

    tracker = VoltCompletionTracker()
    engine.subscribe_tracker(tracker)

    engine.handle_voltage_update(old_voltage=0, new_voltage=120)
    VoltCompletionTracker.queue.get()

    _finish_test("voltage from 0 -> 120")
    # time.sleep(4)

    out_1 = IStateManager.get_state_manager_by_key(3)

    out_1.shut_down()
    engine.handle_state_update(asset_key=out_1.key, old_state=1, new_state=0)

    VoltCompletionTracker.queue.get()

    _finish_test("asset number 2 went down")

    # out_1.power_up()
    # engine.handle_state_update(asset_key=out_1.key, old_state=0, new_state=1)

    # VoltCompletionTracker.queue.get()
    # print("\n\n[TEST] finished 1 up\n\n")

    time.sleep(1000)
