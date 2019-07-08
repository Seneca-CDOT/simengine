"""Steps for testing UPS battery transfer logic and UPS snmp interface reporting correct
OID key/value pairs
"""
import logging
import time

from hamcrest import *

# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import
from behave import given, when, then, step
from test_helpers import query_snmp_interface


def _check_volt_threshold(context, threshold, old_volt, volt_change):

    # query snmp to grab oid and threshold oid value
    th_oid = context.ups.state.get_oid_by_name(threshold).oid
    th_value = query_snmp_interface(th_oid)

    new_volt = int(th_value) + volt_change
    context.engine.handle_voltage_update(old_voltage=old_volt, new_voltage=new_volt)

    # wait for completion of event loop
    if new_volt != old_volt:
        event = context.tracker.load_done_queue.get()
        logging.info(event)


@when('voltage "{old_volt:d}" drops below "{low_th}" threshold by "{volt_change:d}"')
def step_impl(context, low_th, old_volt, volt_change):
    _check_volt_threshold(context, low_th, old_volt, -volt_change)


@when('voltage "{old_volt:d}" spikes above "{high_th}" threshold by "{volt_change:d}"')
def step_impl(context, high_th, old_volt, volt_change):
    _check_volt_threshold(context, high_th, old_volt, volt_change)


@then('UPS "{key:d}" is "{expected_state}" battery')
def step_impl(context, key, expected_state):
    on_battery = context.hardware[key].state.on_battery
    assert_that(on_battery if expected_state == "on" else not on_battery)


@then('UPS "{key:d}" transfer reason is set to "{t_reason}"')
def step_impl(context, key, t_reason):
    # Test both snmp interface and ups instance
    transfer_reason_oid = context.ups.state.get_oid_by_name("InputLineFailCause").oid
    varbind_value = query_snmp_interface(transfer_reason_oid)

    assert_that(context.hardware[key].state.transfer_reason.name, equal_to(t_reason))
    assert_that(
        context.hardware[key].state.InputLineFailCause(varbind_value).name,
        equal_to(t_reason),
    )


@then('after "{seconds:d}" seconds, the transfer reason is set to "{t_reason}"')
def step_impl(context, seconds, t_reason):
    time.sleep(seconds + 1)
    assert context.ups.state.transfer_reason.name == t_reason
