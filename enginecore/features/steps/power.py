# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import
import logging
import os
import queue
import sys
import time
from queue import Queue

from threading import Thread, Event
from circuits import Component, handler, Manager

from behave import given, when, then, step
from hamcrest import *

from enginecore.state.net.ws_requests import ServerToClientRequests
from enginecore.state.new_engine import Engine

from test_helpers import configure_logger


class TestCompletionTracker(Component):

    queue = None

    @handler("VoltageBranchCompleted")
    def on_volt_branch_done(self, event, *args, **kwargs):
        logging.info("Completed event tracking!")
        logging.info(event)
        self.queue.put(event)


@given("Engine is up and running")
def step_impl(context):

    configure_logger()

    os.environ["SIMENGINE_WORKPLACE_TEMP"] = "simengine-test"

    # Start up simengine (in a thread)
    context.engine = Engine()
    context.engine.start()

    context.tracker = TestCompletionTracker()
    context.tracker.queue = Queue()

    context.engine.subscribe_tracker(context.tracker)

    context.engine.handle_voltage_update(old_voltage=0, new_voltage=120)
    logging.info("handled htat!")

    e = context.tracker.queue.get()
    print("\n" * 20)
    logging.info(e)


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
