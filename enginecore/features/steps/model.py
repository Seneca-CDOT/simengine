"""Implementation of feature steps for modelling topology
(creating/connecting hardware assets)
"""

# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import,unused-wildcard-import, wildcard-import
import json
from behave import given, when, then, step

# plyint: enable=no-name-in-module
from hamcrest import *

import enginecore.model.system_modeler as sm
from enginecore.state.api.state import IStateManager


@given("the system model is empty")
def step_impl(context):
    sm.drop_model()
    context.hardware = {}
    IStateManager.get_state_manager_by_key.cache_clear()


@given('Outlet asset with key "{key:d}" is created')
def step_impl(context, key):
    sm.create_outlet(key, {})
    context.hardware[key] = IStateManager.get_state_manager_by_key(key)


@given(
    'PDU asset with key "{key:d}",  minimum "{min_volt:d}" Voltage and "{port:d}" port is created'
)
def step_impl(context, key, min_volt, port):
    sm.create_pdu(key, {"min_voltage": min_volt, "host": "127.0.0.1", "port": port})
    context.hardware[key] = IStateManager.get_state_manager_by_key(key)

    for child_key in context.hardware[key].asset_info["children"]:
        context.hardware[child_key] = IStateManager.get_state_manager_by_key(child_key)


@given('UPS asset with key "{key:d}" and "{port:d}" port is created')
def step_impl(context, key, port):

    sm.create_ups(
        key,
        {
            "power_source": 120,
            "power_consumption": 24,
            "host": "localhost",
            "port": port,
        },
    )

    context.hardware[key] = IStateManager.get_state_manager_by_key(key)
    for child_key in context.hardware[key].asset_info["children"]:
        context.hardware[child_key] = IStateManager.get_state_manager_by_key(child_key)


@given('UPS "{key:d}" has the following runtime graph')
def step_impl(context, key):
    wattage_runtime_map = {}
    for row in context.table:
        wattage_runtime_map[row["wattage"]] = int(row["minutes"])

    sm.configure_asset(key, {"runtime": json.dumps(wattage_runtime_map)})


def _add_server_to_context(context, key):
    context.hardware[key] = IStateManager.get_state_manager_by_key(key)
    for psu_key in context.hardware[key].asset_info["children"]:
        context.hardware[psu_key] = IStateManager.get_state_manager_by_key(psu_key)


@given(
    'Server asset with key "{key:d}", "{psu_num:d}" PSU(s) and "{wattage:d}" Wattage is created'
)
def step_impl(context, key, psu_num, wattage):

    sm.create_server(
        key,
        {
            "domain_name": context.config.userdata["test_vm"],
            "psu_num": psu_num,
            "psu_load": [1 / psu_num for _ in range(psu_num)],
            "power_consumption": wattage,
            "psu_power_consumption": 0,
            "psu_power_source": 120,
        },
        server_variation=sm.ServerVariations.Server,
    )

    _add_server_to_context(context, key)


@given('ServerBMC asset with key "{key:d}" and "{wattage:d}" Wattage is created')
def step_impl(context, key, wattage):

    sm.create_server(
        key,
        {
            "domain_name": context.config.userdata["test_vm"],
            "power_consumption": wattage,
            "psu_power_consumption": 0,
            "psu_power_source": 120,
            "storcli_enabled": False,
        },
        server_variation=sm.ServerVariations.ServerWithBMC,
    )

    _add_server_to_context(context, key)


@given(
    'ServerBMC asset with key "{key:d}" and "{wattage:d}" Wattage and storcli64 support is created'
)
def step_impl(context, key, wattage):

    sm.create_server(
        key,
        {
            "domain_name": context.config.userdata["test_vm"],
            "power_consumption": wattage,
            "psu_power_consumption": 0,
            "psu_power_source": 120,
            "storcli_enabled": True,
            "storcli_port": 50000,
        },
        server_variation=sm.ServerVariations.ServerWithBMC,
    )

    _add_server_to_context(context, key)


@given(
    'Lamp asset with key "{key:d}", minimum "{min_volt:d}" Voltage and "{wattage:d}" Wattage is created'
)
def step_impl(context, key, min_volt, wattage):
    sm.create_lamp(key, {"power_consumption": wattage, "min_voltage": min_volt})
    context.hardware[key] = IStateManager.get_state_manager_by_key(key)


@given('asset "{source_key:d}" powers target "{dest_key:d}"')
def step_impl(context, source_key, dest_key):

    assert_that(source_key, is_in(context.hardware))
    assert_that(dest_key, is_in(context.hardware))

    sm.link_assets(source_key, dest_key)


@given('asset "{key:d}" "{ac_config}" when AC is restored')
def step_impl(_, key, ac_config):
    should_power_on = ac_config == "powers on"
    sm.configure_asset(key, {"power_on_ac": should_power_on})
