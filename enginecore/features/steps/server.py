"""Implementation of feature steps for server and VM management
"""

# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import,unused-wildcard-import, wildcard-import
import logging
import os
import sys
import time

import libvirt
from behave import given, when, then, step
from hamcrest import *


@then('asset "{key:d}" vm is "{vm_state}"')
def step_impl(context, key, vm_state):
    conn = libvirt.open("qemu:///system")
    vm = conn.lookupByName(context.config.userdata["test_vm"])
    assert_that(vm.isActive(), is_(vm_state == "online"))

    conn.close()
