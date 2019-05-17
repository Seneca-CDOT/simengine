# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import
from behave import given, when, then, step
from pysnmp import hlapi
from circuits import Component, handler
import time

# plyint: enable=no-name-in-module

from enginecore.state.api.state import IStateManager
from enginecore.model.system_modeler import create_ups, drop_model
from enginecore.state.hardware.ups_asset import UPS
from enginecore.state.hardware.asset_events import VoltageDecreased, VoltageIncreased

import enginecore.state.state_initializer as state_ini


def query_oid_value(oid):
    error_indicator, error_status, error_idx, var_binds = next(
        hlapi.getCmd(
            hlapi.SnmpEngine(),
            hlapi.CommunityData("public", mpModel=0),
            hlapi.UdpTransportTarget(("localhost", 1024)),
            hlapi.ContextData(),
            hlapi.ObjectType(hlapi.ObjectIdentity(oid)),
            lookupMib=False,
        )
    )

    if error_indicator:
        print(error_indicator)
    elif error_status:
        print(
            "%s at %s"
            % (
                error_status.prettyPrint(),
                error_idx and var_binds[int(error_idx) - 1][0] or "?",
            )
        )
    else:
        v_bind = var_binds[0]
        return v_bind[1]

    return None


@handler("VoltageDecreased")
def on_foo(self):
    print("Hello World!")


class FakeEngine(Component):
    def __init__(self, asset):
        super(FakeEngine, self).__init__()
        self._q_events = None
        asset.register(self)
        self._asset = asset

    def VoltageDecreased_complete(self, evt, e_result):
        # self._asset.unregister(self)
        self.stop()

    def VoltageIncreased_complete(self, evt, e_result):
        # self._asset.unregister(self)

        self.stop()

    def queue_event(self, event):
        self._q_events = event

    def started(self, _):
        self.fire(self._q_events, self._asset)


@given("the system model is empty")
def step_impl(context):
    # configure state
    drop_model()


@given('UPS asset with key "{key:d}" is created')
def step_impl(context, key):

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


@when('voltage drops below "{low_threshold}" threshold by "{volt:d}"')
def step_impl(context, low_threshold, volt):
    low_th_oid = context.ups.state.get_oid_by_name(low_threshold).oid
    low_th_value = query_oid_value(low_th_oid)

    assert low_th_value > 0

    voltage_event = VoltageDecreased(old_value=120, new_value=int(low_th_value) - volt)
    context.engine.queue_event(voltage_event)
    context.engine.run()


@when('voltage spikes above "{high_threshold}" threshold by "{volt:d}"')
def step_impl(context, high_threshold, volt):
    high_oid = context.ups.state.get_oid_by_name(high_threshold).oid
    high_value = query_oid_value(high_oid)

    assert high_value > 0

    context.voltage_event = VoltageIncreased(
        old_value=120, new_value=int(high_value) + volt
    )
    context.engine.queue_event(context.voltage_event)
    context.engine.run()


@then('ups transfers to battery with reason "{t_reason}"')
def step_impl(context, t_reason):
    assert context.ups.state.on_battery
    assert context.ups.state.get_transfer_reason().name == t_reason


@then('after "{seconds:d}" seconds, the transfer reason is set to "{t_reason}"')
def step_impl(context, seconds, t_reason):
    time.sleep(seconds + 1)
    assert context.ups.state.get_transfer_reason().name == t_reason
