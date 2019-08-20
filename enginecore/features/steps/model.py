# pylint: disable=no-name-in-module,function-redefined,missing-docstring,unused-import
from behave import given, when, then, step

# plyint: enable=no-name-in-module

import enginecore.model.system_modeler as sm


@given("the system model is empty")
def step_impl(_):
    sm.drop_model()
