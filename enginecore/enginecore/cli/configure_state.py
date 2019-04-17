"""MISC: exposes various system's state props configurations """
import argparse

from enginecore.state.net.state_client import StateClient
from enginecore.state.api import IStateManager, IUPSStateManager, ISystemEnvironment


def configure_command(configure_state_group):
    """Update some runtime values of the system components"""

    conf_state_subp = configure_state_group.add_subparsers()
    conf_ups_action = conf_state_subp.add_parser(
        "ups", help="Update UPS runtime properties"
    )
    conf_ups_action.add_argument(
        "-k", "--asset-key", type=int, required=True, help="Unique asset key of the UPS"
    )

    conf_ups_action.add_argument(
        "-d",
        "--drain-speed",
        type=float,
        help="Update factor of the battery drain (1 sets to regular speed)",
        choices=range(1, 101),
        metavar="[1-101]",
    )

    conf_ups_action.add_argument(
        "-c",
        "--charge-speed",
        type=float,
        help="Update factor of the battery charge (1 sets to regular speed)",
        choices=range(1, 101),
        metavar="[1-101]",
    )

    conf_sensor_action = conf_state_subp.add_parser(
        "sensor", help="Update sensor runtime properties"
    )
    conf_sensor_action.add_argument(
        "-k",
        "--asset-key",
        type=int,
        required=True,
        help="Unique asset key of the server sensor belongs to",
    )

    conf_sensor_action.add_argument(
        "-s", "--sensor-name", type=str, required=True, help="Name of the sensor"
    )

    conf_sensor_action.add_argument(
        "-r",
        "--runtime-value",
        required=True,
        help="New sensor value (will be reflected on ipmi)",
    )

    conf_ups_action.set_defaults(
        func=lambda args: configure_battery(args["asset_key"], args)
    )
    conf_sensor_action.set_defaults(
        func=lambda args: StateClient(args["asset_key"]).set_sensor_status(
            args["sensor_name"], args["runtime_value"]
        )
    )

    conf_rand_action = conf_state_subp.add_parser(
        "randomizer", help="Configure randomized options for actions"
    )

    conf_rand_action.add_argument(
        "-k",
        "--asset-key",
        type=int,
        help="Unique asset key (Required if randomized options are associated with an asset)",
    )

    conf_rand_action.add_argument(
        "-s",
        "--start",
        type=int,
        required=True,
        help="Start range value for randomized option",
    )

    conf_rand_action.add_argument(
        "-e",
        "--end",
        type=int,
        required=True,
        help="End range value for randomized option",
    )

    conf_rand_action.add_argument(
        "-o",
        "--option",
        required=True,
        help="Option/Argument to be configured",
        choices=[
            "pd-media-error-count",
            "pd-other-error-count",
            "pd-predictive-error-count",
            "ctrl-memory-correctable-errors",
            "ctrl-memory-uncorrectable-errors",
            "ambient",
        ],
    )

    conf_rand_action.set_defaults(validate=validate_randomizer_options)

    conf_rand_action.set_defaults(
        func=lambda args: ISystemEnvironment.set_ambient_props(args)
    )


def validate_randomizer_options(args):
    """Check if asset key was supplied for some options"""
    if args["option"] != "ambient" and not args["asset_key"]:
        raise argparse.ArgumentTypeError(
            'Asset key is required for "{option}" option!'.format(**args)
        )


def configure_battery(key, kwargs):
    """Udpate runtime battery status"""

    state_manager = IStateManager.get_state_manager_by_key(key)

    if not isinstance(state_manager, IUPSStateManager):
        raise argparse.ArgumentTypeError("Asset [{}] is not a ups!".format(key))

    if (kwargs["drain_speed"] and kwargs["charge_speed"]) is None:
        raise argparse.ArgumentTypeError(
            'Must provide "--drain-speed" or "--charge-speed"'
        )

    if kwargs["drain_speed"] is not None:
        state_manager.set_drain_speed_factor(kwargs["drain_speed"])
    if kwargs["charge_speed"] is not None:
        state_manager.set_charge_speed_factor(kwargs["charge_speed"])
