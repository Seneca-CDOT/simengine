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


def _check_ipmi_sensor_value(ipmi_config, sensor_name):
    """Query ipmi interface given ipmi host, port, user, password
    and retrieve sensor value for a specific sensor
    """
    query = "/usr/bin/ipmitool "
    query += "-H {host} -p {port} -U {user} -P {password} sdr list".format(
        **ipmi_config
    )
    query += ' | grep "' + sensor_name + '"'

    ipmi_out = subprocess.check_output(query, shell=True).decode("utf-8")
    if not ipmi_out:
        return ""

    s_value = ipmi_out.split("|")[1]
    return s_value.strip()


@then('asset "{key:d}" BMC sensor "{sensor_name}" value is "{e_value}"')
def step_impl(context, key, sensor_name, e_value):
    asset_info = context.hardware[key].asset_info
    s_value = _check_ipmi_sensor_value(asset_info, sensor_name)
    assert_that(s_value, equal_to(e_value))
