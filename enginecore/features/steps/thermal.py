# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import

import time

from behave import given, when, then, step
from hamcrest import *
from enginecore.state.api.environment import ISystemEnvironment


@given("server room has the following ambient properties")
def step_impl(context):
    for row in context.table.rows:
        amb_props = {context.table.headings[i]: v for i, v in enumerate(row)}

        for num_prop in ["degrees", "rate", "pause_at"]:
            amb_props[num_prop] = int(amb_props[num_prop])

        ISystemEnvironment.set_ambient_props(amb_props)


@given('ambient is "{temp:d}" degrees')
def step_impl(context, temp):
    ISystemEnvironment.set_ambient(temp)


@then('ambient is set to "{temp:d}" after "{delay:d}" seconds')
def step_impl(context, temp, delay):
    time.sleep(delay)
    ambient = ISystemEnvironment.get_ambient()
    assert_that(ambient, equal_to(temp))
