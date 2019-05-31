# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import
from behave import given, when, then, step

# plyint: enable=no-name-in-module

import enginecore.model.system_modeler as sm


@given("the system model is empty")
def step_impl(_):
    sm.drop_model()


@given('"{asset_type}" asset with key "{key:d}" is created')
def step_impl(context, key):

    if not hasattr(context, "num_assets"):
        context.num_assets = 0

    type_map = {
        "UPS": sm.create_ups,
        "PDU": sm.create_pdu,
        "Server": sm.create_server,
        "Outlet": sm.create_outlet,
    }

    attr_map = {
        "snmp_device": {
            "work_dir": "/tmp/simengine-test",
            "power_source": 120,
            "power_consumption": 24,
            "host": "localhost",
            "port": 1024,
        }
    }

    create_ups(
        key,
        {
            "work_dir": "/tmp/simengine-test",
            "power_source": 120,
            "power_consumption": 24,
            "host": "localhost",
            "port": 1024,
        },
    )

    state_ini.configure_env(relative=True)
    state_ini.initialize(force_snmp_init=True)

    context.ups = UPS(IStateManager.get_state_manager_by_key(key).asset_info)
    context.ups.start()
    context.engine = FakeEngine(context.ups)

    assert context.ups.state.status == 1
    assert context.ups.state.agent[1]
