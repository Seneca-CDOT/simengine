#!/usr/bin/python3
"""Entry point initializing platform environment, state listeners
and state handlers (engine)
"""

import argparse
import os
import sys
import logging
from logging import handlers

from enginecore.state.redis_state_listener import StateListener
from enginecore.state.engine.engine import Engine
import enginecore

FORMAT = "[%(threadName)s, %(asctime)s, %(module)s:%(lineno)s] %(message)s"
DEV_FORMAT = "[%(threadName)s, %(asctime)s, %(module)s:%(lineno)s] %(message)s"


def configure_logger(develop=False, debug=False):
    """Configure logger instance for the simengine app
    Args:
        develop(bool): indicates logger variant
                       (logger will use relative paths if set to true)
        debug(bool): set logger level to debugging
    """

    logger = logging.getLogger(enginecore.__name__)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    formatter = logging.Formatter(DEV_FORMAT, "%H:%M:%S" if develop else FORMAT)

    # neo4j logs to much info, disable DEBUG-level logging
    if debug:
        neo4j_log = logging.getLogger("neo4j.bolt")
        neo4j_log.setLevel(logging.WARNING)

    if develop:
        log_path = "info.log"
        stdout_h = logging.StreamHandler(sys.stdout)
        stdout_h.setFormatter(formatter)

        logger.addHandler(stdout_h)
    else:
        log_path = os.path.join(os.sep, "var", "log", "simengine", "info.log")

    logfile_h = handlers.RotatingFileHandler(
        log_path, maxBytes=10 * 1024 * 1024, backupCount=5
    )

    logfile_h.setFormatter(formatter)
    logger.addHandler(logfile_h)


def run_app():
    """
    Initialize components' states in redis based on a reference model
    & launch event listener daemon
    """

    # parse cli option
    argparser = argparse.ArgumentParser(
        description="Start enginecore daemon running the main engine loop"
    )

    argparser.add_argument(
        "-v", "--verbose", help="Enable State Listener Debugger", action="store_true"
    )
    argparser.add_argument(
        "-r",
        "--reload-data",
        help="Reload state data from .snmprec files",
        action="store_true",
    )
    argparser.add_argument(
        "-d", "--develop", help="Run in a development mode", action="store_true"
    )

    args = vars(argparser.parse_args())

    # logging config
    configure_logger(develop=args["develop"], debug=args["verbose"])

    # run daemon
    StateListener(
        engine_cls=Engine, debug=args["verbose"], force_snmp_init=args["reload_data"]
    ).run()


if __name__ == "__main__":
    run_app()
