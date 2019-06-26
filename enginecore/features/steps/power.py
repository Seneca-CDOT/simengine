# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import
import logging
import os
import queue
import sys
import time

from threading import Thread, Event
from circuits import Component, handler

from behave import given, when, then, step
from hamcrest import *

from enginecore.state.net.ws_requests import ServerToClientRequests
from enginecore.state.new_engine import Engine

from test_helpers import configure_logger


class TestCompletionTracker(Component):

    event = None

    @handler("VoltageBranchCompleted")
    def on_volt_branch_done(self, event, *args, **kwargs):
        TestCompletionTracker.event.set()


@given("Engine is up and running")
def step_impl(context):

    configure_logger()

    os.environ["SIMENGINE_WORKPLACE_TEMP"] = "simengine-test"

    if "engine" in context:
        print(context.engine)

    # Start up simengine (in a thread)
    context.engine = Engine()

    context.engine.start()

    context.tracker = TestCompletionTracker()
    context.tracker.event = Event()

    context.engine.subscribe_tracker(context.tracker)

    context.engine.handle_voltage_update(old_voltage=0, new_voltage=120)

    print(context.tracker.event)
    time.sleep(5)
    # context.tracker.event.wait()


@when('asset "{key:d}" is powered down')
def step_impl(context, key):
    context.hardware[key].shut_down()
    context.engine.handle_state_update(key, 0)


@when('asset "{key:d}" is powered up')
def step_impl(context, key):
    context.hardware[key].power_up()
    context.engine.handle_state_update(key, 1)


@then('asset "{key:d}" load is set to "{load:f}"')
def step_impl(context, key, load):
    assert_that(context.hardware[key].load, close_to(load, 0.0001))


@then('asset "{key:d}" is online')
def step_impl(context, key):
    assert_that(context.hardware[key].status, equal_to(1))


@then('asset "{key:d}" is offline')
def step_impl(context, key):
    assert_that(context.hardware[key].status, equal_to(0))
