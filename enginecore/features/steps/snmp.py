"""A collection of shared utils for BDD tests"""
# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import

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
    """Helper function to query snmp interface of a device"""
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
