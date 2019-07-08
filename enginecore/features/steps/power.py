# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import
import logging
import os
import sys
import time
from queue import Queue

from threading import Thread, Event
from circuits import Component, handler

from behave import given, when, then, step
from hamcrest import *

from enginecore.state.net.ws_requests import ServerToClientRequests
from enginecore.state.new_engine import Engine


class TestCompletionTracker(Component):

    volt_done_queue = None
    load_done_queue = None

    @handler("AllVoltageBranchesDone")
    def on_volt_branch_done(self, event, *args, **kwargs):
        self.volt_done_queue.put(event)

    @handler("AllLoadBranchesDone")
    def on_load_branch_done(self, event, *args, **kwargs):
        self.load_done_queue.put(event)


@given("Engine is up and running")
def step_impl(context):

    os.environ["SIMENGINE_WORKPLACE_TEMP"] = "simengine-test"

    # Start up simengine (in a thread)
    context.engine = Engine()
    context.engine.start()

    context.tracker = TestCompletionTracker()
    context.tracker.volt_done_queue = Queue()
    context.tracker.load_done_queue = Queue()

    context.engine.subscribe_tracker(context.tracker)

    context.engine.handle_voltage_update(old_voltage=0, new_voltage=120)

    event = context.tracker.load_done_queue.get()
    logging.info(event)


@given('wallpower voltage "{old_volt:d}" is set to "{new_volt:d}"')
@when('wallpower voltage "{old_volt:d}" is updated to "{new_volt:d}"')
def step_impl(context, old_volt, new_volt):
    context.engine.handle_voltage_update(old_voltage=old_volt, new_voltage=new_volt)

    # wait for completion of event loop
    if new_volt != old_volt:
        event = context.tracker.load_done_queue.get()
        logging.info(event)


@given('asset "{key:d}" is "{state}"')
@when('asset "{key:d}" goes "{state}"')
def step_impl(context, key, state):

    state_m = context.hardware[key]

    old_state = state_m.status
    new_state = state_m.power_up() if state == "online" else state_m.shut_down()

    context.engine.handle_state_update(key, old_state, new_state)

    if old_state != new_state:
        event = context.tracker.load_done_queue.get()
        logging.info(event)


@then('asset "{key:d}" load is set to "{load:f}"')
def step_impl(context, key, load):
    assert_that(context.hardware[key].load, close_to(load, 0.0001))


@then('asset "{key:d}" is "{state}"')
def step_impl(context, key, state):
    state_num = 1 if state == "online" else 0
    assert_that(context.hardware[key].status, equal_to(state_num))


@then('asset "{key:d}" input voltage is "{volt:d}"')
def step_impl(context, key, volt):
    assert_that(context.hardware[key].input_voltage, equal_to(volt))


@then('asset "{key:d}" output voltage is "{volt:d}"')
def step_impl(context, key, volt):
    assert_that(context.hardware[key].output_voltage, equal_to(volt))
