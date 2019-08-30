"""
Cleanup functionalities for features/scenarios is grouped in this file
see: https://behave.readthedocs.io/en/latest/tutorial.html#environmental-controls
"""
import logging
import sys
import os

from behave import fixture, use_fixture

# plyint: enable=no-name-in-module
def configure_logger(_):
    """Configure logger for debugging purpose"""
    log_format = "[%(threadName)s, %(module)s.%(funcName)s:%(lineno)s] %(message)s"

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    formatter = logging.Formatter(log_format)

    stdout_h = logging.StreamHandler(sys.stdout)
    stdout_h.setFormatter(formatter)

    root.addHandler(stdout_h)


@fixture
def shut_down_threads(context, scenario):
    """Fixture for stopping threads"""

    if hasattr(context, "engine"):
        context.engine.stop()

    if "server-bmc-asset" in scenario.effective_tags:
        os.system("killall ipmi_sim")


def before_all(context):
    """Pre-test configuration"""


#     use_fixture(configure_logger, context)


def after_scenario(context, scenario):
    """Stop threads after each scenario"""
    use_fixture(shut_down_threads, context, scenario)
