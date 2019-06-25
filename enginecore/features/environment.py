"""
Cleanup functionalities for features/scenarios is grouped in this file
see: https://behave.readthedocs.io/en/latest/tutorial.html#environmental-controls
"""

from behave import fixture, use_fixture


@fixture
def shut_down_threads(context):
    """Fixture for stopping threads"""

    if hasattr(context, "engine"):
        context.engine.stop()

    if hasattr(context, "ws_thread") and context.ws_thread.isAlive():
        context.ws_thread.join()


def after_scenario(context, _):
    """Stop threads after each scenario"""
    use_fixture(shut_down_threads, context)
