# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import
from behave import given, when, then, step
from hamcrest import *

# plyint: enable=no-name-in-module


@then('asset "{key:d}" load is set to "{load:f}"')
def step_impl(context, key, load):
    assert_that(context.hardware[key].load, close_to(load, 0.0001))


@then('asset "{key:d}" is online')
def step_impl(context, key):
    assert_that(context.hardware[key].status, equal_to(1))


@then('asset "{key:d}" is offline')
def step_impl(context, key):
    assert_that(context.hardware[key].status, equal_to(0))
