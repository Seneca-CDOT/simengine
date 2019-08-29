"""Implementation of feature steps for server and VM management
"""

# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import,unused-wildcard-import, wildcard-import
import logging
import os
import sys
import time
import subprocess

import libvirt
from behave import given, when, then, step
from hamcrest import *


@then('asset "{key:d}" vm is "{vm_state}"')
def step_impl(context, key, vm_state):
    conn = libvirt.open("qemu:///system")
    vm = conn.lookupByName(context.config.userdata["test_vm"])
    assert_that(vm.isActive(), is_(vm_state == "online"))

    conn.close()


def _get_ipmi_query(ipmi_config):
    """Get ipmi command from a set of LAN configurations"""
    query = "/usr/bin/ipmitool "
    query += "-H {host} -p {port} -U {user} -P {password}".format(**ipmi_config)
    return query


def _check_ipmi_sensor_value(ipmi_config, sensor_name):
    """Query ipmi interface given ipmi host, port, user, password
    and retrieve sensor value for a specific sensor
    """
    query = _get_ipmi_query(ipmi_config) + " sdr list"
    query += ' | grep "' + sensor_name + '"'

    ipmi_out = subprocess.check_output(query, shell=True).decode("utf-8")
    if not ipmi_out:
        return ""

    s_value = ipmi_out.split("|")[1]
    return s_value.strip()


def _check_ipmi_status(ipmi_config):
    """Check status of chassis and IPMI interface
    returns on, off or unreachable
    """

    query = _get_ipmi_query(ipmi_config) + " power status"
    try:
        ipmi_out = subprocess.check_output(query, shell=True).decode("utf-8").strip()
        return ipmi_out.split()[-1]  # get 'on' or 'off' token
    except subprocess.CalledProcessError:
        return "unreachable"


@then('asset "{key:d}" BMC sensor "{sensor_name}" value is "{e_value}"')
def step_impl(context, key, sensor_name, e_value):
    asset_info = context.hardware[key].asset_info
    s_value = _check_ipmi_sensor_value(asset_info, sensor_name)
    assert_that(s_value, equal_to(e_value))


@then('asset "{key:d}" ipmi interface is "{ipmi_status}"')
def step_impl(context, key, ipmi_status):
    asset_info = context.hardware[key].asset_info
    status = _check_ipmi_status(asset_info)

    assert_that(
        status, (is_ if ipmi_status == "unreachable" else is_not)("unreachable")
    )


@then('asset "{key:d}" ipmi chassis status is "{ipmi_status}"')
def step_impl(context, key, ipmi_status):
    asset_info = context.hardware[key].asset_info
    status = _check_ipmi_status(asset_info)
    assert_that(status, is_({"offline": "off", "online": "on"}[ipmi_status]))
