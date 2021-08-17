"""Steps for testing UPS battery transfer logic and UPS snmp interface reporting correct
OID key/value pairs
"""
# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import,unused-wildcard-import, wildcard-import

import logging
import time

from hamcrest import *
from behave import given, when, then, step

from snmp import query_snmp_interface


def _check_volt_threshold(context, key, threshold, old_volt, volt_change):

    # query snmp to grab oid and threshold oid value
    th_oid = context.hardware[key].get_oid_by_name(threshold).oid
    th_value = query_snmp_interface(th_oid)

    new_volt = int(th_value) + volt_change
    context.engine.handle_voltage_update(old_voltage=old_volt, new_voltage=new_volt)

    # wait for completion of event loop
    if new_volt != old_volt:
        event = context.tracker.load_done_queue.get()
        logging.info(event)


@when(
    'voltage "{old_volt:d}" drops below "{low_th}" threshold by "{volt_change:d}" for UPS "{key:d}"'
)
def step_impl(context, old_volt, low_th, volt_change, key):
    _check_volt_threshold(context, key, low_th, old_volt, -volt_change)


@when(
    'voltage "{old_volt:d}" spikes above "{high_th}" threshold by "{volt_change:d}" for UPS "{key:d}"'
)
def step_impl(context, old_volt, high_th, volt_change, key):
    _check_volt_threshold(context, key, high_th, old_volt, volt_change)


@given('UPS "{key:d}" battery "{factor_type}" factor is set to "{factor_num:d}"')
def step_impl(context, key, factor_type, factor_num):
    if factor_type == "drain":
        context.engine.assets[key].drain_speed_factor = factor_num
    else:
        context.engine.assets[key].charge_speed_factor = factor_num


@then('UPS "{key:d}" is "{expected_state}" battery')
def step_impl(context, key, expected_state):
    on_battery = context.hardware[key].on_battery
    assert_that(on_battery if expected_state == "on" else not on_battery)


@then('UPS "{key:d}" battery is "{expected_charge_state}"')
def step_impl(context, key, expected_charge_state):
    """expected_charge_state is either
    'draining' -> battery lvl is dropping
    'charging' -> battery lvl is going up
    'inactive' -> nothing is going on
    """

    ups_asset = context.engine.assets[key]

    inactive = expected_charge_state == "inactive"
    if inactive:
        assert_that(ups_asset.draining_battery, equal_to(False))
        assert_that(ups_asset.charging_battery, equal_to(False))
        return

    should_be_draining = expected_charge_state == "draining"

    assert_that(ups_asset.draining_battery, equal_to(should_be_draining))
    assert_that(ups_asset.charging_battery, not_(equal_to(should_be_draining)))


@then('UPS "{key:d}" transfer reason is set to "{t_reason}"')
def step_impl(context, key, t_reason):
    # Test both snmp interface and ups instance
    transfer_reason_oid = (
        context.hardware[key].get_oid_by_name("InputLineFailCause").oid
    )
    varbind_value = query_snmp_interface(transfer_reason_oid)

    assert_that(context.hardware[key].transfer_reason.name, equal_to(t_reason))
    assert_that(
        context.hardware[key].InputLineFailCause(varbind_value).name, equal_to(t_reason)
    )


@then('after "{seconds:d}" seconds, transfer reason for UPS "{key:d}" is "{t_reason}"')
def step_impl(context, seconds, key, t_reason):

    time.sleep(seconds + 1)
    context.execute_steps(
        'then UPS "{key:d}" transfer reason is set to "{t_reason}"'.format(
            key=key, t_reason=t_reason
        )
    )


@then('UPS "{key:d}" time remaining for battery is "{minutes:d}" minutes')
def step_impl(context, key, minutes):
    transfer_reason_oid = (
        context.hardware[key].get_oid_by_name("BatteryRunTimeRemaining").oid
    )

    convert_to_minutes = lambda ticks: ticks / 6000
    varbind_value = query_snmp_interface(transfer_reason_oid)
    assert_that(minutes, close_to(convert_to_minutes(varbind_value), 0.001))
