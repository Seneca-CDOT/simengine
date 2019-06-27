from circuits import Component, handler
from enginecore.state.new_engine import Engine
from enginecore.state.api.state import IStateManager

import time

engine = Engine()
engine.start()


class VoltCompletionTracker(Component):
    channel = "volt-tracker"

    @handler("VoltageBranchCompleted")
    def pabam(self, event, *args, **kwargs):
        print("\n\n---------> pabam!")


while True:

    tracker = VoltCompletionTracker()
    engine.subscribe_tracker(tracker)

    engine.handle_voltage_update(old_voltage=0, new_voltage=120)
    time.sleep(2)
    print("\n\n[TEST] finished voltage\n\n")

    # out_1 = IStateManager.get_state_manager_by_key(1)

    # out_1.shut_down()
    # engine.handle_state_update(asset_key=out_1.key, old_state=1, new_state=0)

    # time.sleep(2)
    # print("\n\n[TEST] finished 1 down\n\n")

    # out_1.power_up()
    # engine.handle_state_update(asset_key=out_1.key, old_state=0, new_state=1)

    # time.sleep(2)
    # print("\n\n[TEST] finished 1 up\n\n")

    time.sleep(1000)
