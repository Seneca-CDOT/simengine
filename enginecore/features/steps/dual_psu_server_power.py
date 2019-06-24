# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import
import logging
import sys
import time
import os
import json
import math
import queue

from threading import Thread, Event

from behave import given, when, then, step

# plyint: enable=no-name-in-module

from enginecore.model.system_modeler import create_server, create_outlet, link_assets

from enginecore.state.api.state import IStateManager
from enginecore.state.hardware.server_asset import Server
from enginecore.state.net.ws_requests import ServerToClientRequests
from enginecore.state.event_map import PowerEventMap
import enginecore.state.state_initializer as state_ini
from enginecore.state.engine import Engine

from test_helpers import TestClient


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

    # Start up simengine
    context.engine = Engine()
    context.engine.start()

    context.ws_queue = queue.Queue()

    TestClient.context = context
    TestClient.queue = context.ws_queue

    ws_thread = Thread(target=TestClient.client, name="engine-client")
    ws_thread.daemon = True
    ws_thread.start()

    passed = False

    while not passed or not context.ws_queue.empty():
        message = context.ws_queue.get()
        logging.info(
            "Consumer storing message: %s (size=%d)", message, context.ws_queue.qsize()
        )
