# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import
import logging
import sys
import time
import os
import json

from websocket import create_connection
from behave import given, when, then, step

# plyint: enable=no-name-in-module

from enginecore.state.api.state import IStateManager
from enginecore.state.hardware.server_asset import Server

from enginecore.model.system_modeler import create_server, create_outlet, link_assets
from enginecore.state.event_map import PowerEventMap
import enginecore.state.state_initializer as state_ini
from enginecore.state.engine import Engine


def configure_logger():
    DEV_FORMAT = "[%(threadName)s, %(asctime)s, %(module)s:%(lineno)s] %(message)s"

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    formatter = logging.Formatter(DEV_FORMAT)

    stdout_h = logging.StreamHandler(sys.stdout)
    stdout_h.setFormatter(formatter)

    root.addHandler(stdout_h)


@given(
    'Server asset with key "{key:d}", "{psu_num:d}" PSU(s) and "{wattage:d}" Wattage is created'
)
def step_impl(context, key, psu_num, wattage):

    # configure_logger()

    create_server(
        key,
        {
            "domain_name": "an-a01n01",
            "psu_num": psu_num,
            "psu_load": [0.5, 0.5],
            "power_consumption": wattage,
            "psu_power_consumption": 0,
            "psu_power_source": 120,
        },
    )

    context.server = IStateManager.get_state_manager_by_key(key)
    context.psu_1 = IStateManager.get_state_manager_by_key(key * 10 + 1)
    context.psu_2 = IStateManager.get_state_manager_by_key(key * 10 + 2)

    create_outlet(1, {})
    create_outlet(2, {})
    link_assets(1, context.psu_1.key)
    link_assets(2, context.psu_2.key)


@given("Engine is up and running")
def step_impl(context):

    os.environ["SIMENGINE_WORKPLACE_TEMP"] = "simengine-test"

    state_ini.configure_env(relative=True)
    state_ini.initialize(force_snmp_init=True)

    context.engine = Engine()
    context.engine.start()  # run
    context.engine.handle_voltage_update(0, 120)

    ws = create_connection("ws://0.0.0.0:8000/simengine")
    json.dumps({"request": "subscribe", "payload": {}})
    print("Sent")
    print("Receiving...")
    result = ws.recv()
    print("Received '%s'" % result)
    ws.close()

    print(context.psu_1)
    print(context.psu_2)
    print(context.server)

    # assert context.ups.state.transfer_reason.name == 1
