# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import
from behave import given, when, then, step

# plyint: enable=no-name-in-module

import enginecore.model.system_modeler as sm
from enginecore.state.api.state import IStateManager
from hamcrest import *

TEST_VM_NAME = "an-a01n01"


@given("the system model is empty")
def step_impl(context):
    sm.drop_model()
    context.hardware = {}


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


@given(
    'Server asset with key "{key:d}", "{psu_num:d}" PSU(s) and "{wattage:d}" Wattage is created'
)
def step_impl(context, key, psu_num, wattage):

    sm.create_server(
        key,
        {
            "domain_name": TEST_VM_NAME,
            "psu_num": psu_num,
            "psu_load": [0.5, 0.5],
            "power_consumption": wattage,
            "psu_power_consumption": 0,
            "psu_power_source": 120,
        },
    )

    context.hardware[key] = IStateManager.get_state_manager_by_key(key)
    psu_key_1 = key * 10 + 1
    psu_key_2 = key * 10 + 2

    context.hardware[psu_key_1] = IStateManager.get_state_manager_by_key(psu_key_1)
    context.hardware[psu_key_2] = IStateManager.get_state_manager_by_key(psu_key_2)


@given(
    'Lamp asset with key "{key:d}", minimum "{min_volt:d}" Voltage and "{wattage:d}" Wattage is created'
)
def step_impl(context, key, min_volt, wattage):
    sm.create_lamp(key, {"power_consumption": wattage, "min_voltage": min_volt})
    context.hardware[key] = IStateManager.get_state_manager_by_key(key)


@given('asset "{source_key:d}" powers target "{dest_key:d}"')
def step_impl(context, source_key, dest_key):

    # print(context.hardware)
    assert_that(source_key, is_in(context.hardware))
    assert_that(dest_key, is_in(context.hardware))

    sm.link_assets(source_key, dest_key)
