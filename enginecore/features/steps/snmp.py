"""Implementation of feature steps for managing/querying SNMP state
of hardware assets that support SNMP interface (UPS/PDU etc.)
"""

# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import,unused-wildcard-import, wildcard-import

import time
from pysnmp import hlapi
from behave import given, when, then, step

from hamcrest import *
from pysnmp.proto.rfc1902 import *


def query_snmp_interface(oid, host="localhost", port=1024):
    """Helper function to query snmp interface of a device"""
    error_indicator, error_status, error_idx, var_binds = next(
        hlapi.getCmd(
            hlapi.SnmpEngine(),
            hlapi.CommunityData("private", mpModel=0),
            hlapi.UdpTransportTarget((host, port)),
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


def set_oid_value(oid, value, host="localhost", port=1024):
    """Helper function to set snmp oid value of a device"""
    error_indicator, error_status, error_idx, var_binds = next(
        hlapi.setCmd(
            hlapi.SnmpEngine(),
            hlapi.CommunityData("private", mpModel=0),
            hlapi.UdpTransportTarget((host, port)),
            hlapi.ContextData(),
            hlapi.ObjectType(hlapi.ObjectIdentity(oid), value),
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


@when('asset "{key:d}" oid "{oid_num}" is set to "{oid_value}"')
def step_impl(context, key, oid_num, oid_value):

    snmp_asset_info = context.hardware[key].asset_info

    set_oid_value(
        oid_num,
        Integer32(oid_value),
        host=snmp_asset_info["host"],
        port=snmp_asset_info["port"],
    )

    context.engine.handle_oid_update(key, oid_num, oid_value)
    context.tracker.wait_load_queue()


@then('asset "{key:d}" oid "{oid_num}" is set to "{oid_value}"')
def step_impl(context, key, oid_num, oid_value):

    snmp_asset_info = context.hardware[key].asset_info

    oid_response = query_snmp_interface(
        oid_num, host=snmp_asset_info["host"], port=snmp_asset_info["port"]
    )

    assert_that(str(oid_response), equal_to(oid_value))


def _ping_snmp(snmp_asset_info, snmp_state):
    """Verify SNMP interface availability given host/port & the desirable state"""
    res = query_snmp_interface(
        oid="1.3.6.1.2.1.1.5.0",
        host=snmp_asset_info["host"],
        port=snmp_asset_info["port"],
    )

    assert_that(res, (none if snmp_state == "unreachable" else not_none)())


@then('SNMP interface for asset "{key:d}" is "{snmp_state}"')
def step_impl(context, key, snmp_state):
    _ping_snmp(context.hardware[key].asset_info, snmp_state)


@then(
    'after "{seconds:d}" seconds, SNMP interface for asset "{key:d}" is "{snmp_state}"'
)
def step_impl(context, seconds, key, snmp_state):
    time.sleep(seconds)
    _ping_snmp(context.hardware[key].asset_info, snmp_state)
