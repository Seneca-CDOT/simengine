# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import
import logging
import os
import queue
import sys
from threading import Thread

from behave import given, when, then, step
from hamcrest import *

from enginecore.state.net.ws_requests import ServerToClientRequests
import enginecore.state.state_initializer as state_ini
from enginecore.state.engine import Engine

from test_helpers import TestClient

# plyint: enable=no-name-in-module
def configure_logger():
    log_format = "[%(threadName)s, %(asctime)s, %(module)s:%(lineno)s] %(message)s"

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    formatter = logging.Formatter(log_format)

    stdout_h = logging.StreamHandler(sys.stdout)
    stdout_h.setFormatter(formatter)

    root.addHandler(stdout_h)


@given("Engine is up and running")
def step_impl(context):

    configure_logger()

    os.environ["SIMENGINE_WORKPLACE_TEMP"] = "simengine-test"

    state_ini.configure_env(relative=True)
    state_ini.initialize(force_snmp_init=True)

    if "engine" in context:
        print(context.engine)
    # Start up simengine
    context.engine = Engine()
    context.engine.start()

    context.ws_queue = queue.Queue()
    context.ws_client = TestClient()

    TestClient.context = context
    TestClient.queue = context.ws_queue

    TestClient.ws_thread = Thread(
        target=context.ws_client.run_client, name="engine-client"
    )
    TestClient.ws_thread.daemon = True
    TestClient.ws_thread.start()

    loop_done_num = 0
    num_mains_outs = len(context.engine.mains_out_keys)

    while loop_done_num != num_mains_outs or not context.ws_queue.empty():

        message = context.ws_queue.get()
        logging.info("Consumer storing message: %s (size=%d)", message, num_mains_outs)

        if message["request"] == ServerToClientRequests.load_loop_done.name:
            loop_done_num = loop_done_num + 1


@when('asset "{key:d}" is powered down')
def step_impl(context, key):
    context.hardware[key].shut_down()
    context.engine.handle_state_update(key, 0)
    import time

    # time.sleep(2)


@when('asset "{key:d}" is powered up')
def step_impl(context, key):
    context.hardware[key].power_up()
    context.engine.handle_state_update(key, 1)
    import time

    # time.sleep(2)


@then('asset "{key:d}" load is set to "{load:f}"')
def step_impl(context, key, load):
    assert_that(context.hardware[key].load, close_to(load, 0.0001))


@then('asset "{key:d}" is online')
def step_impl(context, key):
    assert_that(context.hardware[key].status, equal_to(1))


@then('asset "{key:d}" is offline')
def step_impl(context, key):
    assert_that(context.hardware[key].status, equal_to(0))
