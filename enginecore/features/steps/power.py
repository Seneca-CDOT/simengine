"""Implementation of feature steps for managing system power
(power outages/hardware power states etc.)
"""

# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import,unused-wildcard-import, wildcard-import
import logging
import os
import sys
import time
from queue import Queue

from threading import Thread, Event
from circuits import Component, handler

from behave import given, when, then, step
from hamcrest import *

from enginecore.state.state_initializer import configure_env
from enginecore.state.engine.engine import Engine
from enginecore.state.api.environment import ISystemEnvironment


class TestCompletionTracker(Component):
    """Track completion of power iterations happening in the engine"""

    volt_done_queue = None
    load_done_queue = None
    th_done_queue = None

    def __init__(self, timeout):

        super().__init__()
        self._timeout = None if timeout < 0 else timeout

        self.volt_done_queue = Queue()
        self.load_done_queue = Queue()
        self.th_done_queue = Queue()

    # pylint: disable=unused-argument
    @handler("AllVoltageBranchesDone")
    def on_volt_branch_done(self, event, *args, **kwargs):
        self.volt_done_queue.put(event)

    @handler("AllLoadBranchesDone")
    def on_load_branch_done(self, event, *args, **kwargs):
        """Wait for engine to complete a power iteration"""
        self.load_done_queue.put(event)

    @handler("AllThermalBranchesDone")
    def on_th_branch_done(self, event, *args, **kwargs):
        self.th_done_queue.put(event)

    # pylint: enable=unused-argument

    def wait_load_queue(self):
        return self.load_done_queue.get(timeout=self._timeout)

    def wait_thermal_queue(self):
        return self.th_done_queue.get(timeout=self._timeout)


@then("Engine is up and running")
@given("Engine is up and running")
def step_impl(context):

    os.environ["SIMENGINE_WORKPLACE_TEMP"] = context.config.userdata["tmp_simengine"]

    # Start up simengine (in a thread)
    configure_env(relative=True)
    context.engine = Engine()
    context.engine.start()

    context.tracker = TestCompletionTracker(
        int(context.config.userdata["engine_timeout"])
    )

    context.engine.subscribe_tracker(context.tracker)

    context.engine.handle_voltage_update(old_voltage=0, new_voltage=120)

    logging.info(context.tracker.wait_load_queue())


@when('pause for "{delay:d}" seconds')
def step_impl(_, delay):
    time.sleep(delay)


@when("power outage happens")
def step_impl(context):

    if ISystemEnvironment.mains_status():
        ISystemEnvironment.power_outage()
        context.engine.handle_voltage_update(old_voltage=120, new_voltage=0)
        logging.info(context.tracker.wait_load_queue())


@when("power is restored")
def step_impl(context):

    if not ISystemEnvironment.mains_status():
        ISystemEnvironment.power_restore()
        context.engine.handle_voltage_update(old_voltage=0, new_voltage=120)
        logging.info(context.tracker.wait_load_queue())


@given('wallpower voltage is set to "{new_volt:d}"')
@when('wallpower voltage is updated to "{new_volt:d}"')
def step_impl(context, new_volt):

    old_volt = ISystemEnvironment.get_voltage()
    ISystemEnvironment.set_voltage(new_volt)

    context.engine.handle_voltage_update(old_voltage=old_volt, new_voltage=new_volt)

    # wait for completion of event loop
    if new_volt != old_volt:
        logging.info(context.tracker.wait_load_queue())


@given('asset "{key:d}" is "{state}"')
@when('asset "{key:d}" goes "{state}"')
def step_impl(context, key, state):

    state_m = context.hardware[key]

    old_state = state_m.status

    if state == "online":
        new_state = state_m.power_up()
    else:
        new_state = state_m.shut_down()

    context.engine.handle_state_update(key, old_state, new_state)

    if old_state != new_state:
        logging.info(context.tracker.wait_load_queue())


@then('asset "{key:d}" load is set to "{load:f}"')
def step_impl(context, key, load):
    assert_that(context.hardware[key].load, close_to(load, 0.0001))


@then('asset "{key:d}" is "{state}"')
def step_impl(context, key, state):
    state_num = 1 if state == "online" else 0
    assert_that(context.hardware[key].status, equal_to(state_num))


@then('after "{seconds:d}" seconds, asset "{key:d}" is "{state}"')
def step_impl(context, seconds, key, state):
    time.sleep(seconds)
    state_num = 1 if state == "online" else 0
    assert_that(context.hardware[key].status, equal_to(state_num))


@then('asset "{key:d}" input voltage is "{volt:d}"')
def step_impl(context, key, volt):
    assert_that(context.hardware[key].input_voltage, equal_to(volt))


@then('asset "{key:d}" output voltage is "{volt:d}"')
def step_impl(context, key, volt):
    assert_that(context.hardware[key].output_voltage, equal_to(volt))
