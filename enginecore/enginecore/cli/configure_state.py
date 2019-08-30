"""MISC: exposes various system's state props configurations """
import argparse

from enginecore.state.net.state_client import StateClient
from enginecore.state.api import (
    IStateManager,
    IUPSStateManager,
    ISystemEnvironment,
    IBMCServerStateManager,
)


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
        choices=range(1, 10001),
        metavar="[1-10001]",
    )

    conf_ups_action.add_argument(
        "-c",
        "--charge-speed",
        type=float,
        help="Update factor of the battery charge (1 sets to regular speed)",
        choices=range(1, 10001),
        metavar="[1-10001]",
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
        help="Unique asset key (Required if randomized \
             options are associated with an asset)",
    )

    conf_rand_action.add_argument(
        "-s", "--start", type=int, help="Start range value for randomized option"
    )

    conf_rand_action.add_argument(
        "-e", "--end", type=int, help="End range value for randomized option"
    )

    conf_rand_action.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List randranges for ranomizable options",
    )

    conf_rand_arguments = [
        "pd-media-error-count",
        "pd-other-error-count",
        "pd-predictive-error-count",
        "ctrl-memory-correctable-errors",
        "ctrl-memory-uncorrectable-errors",
        "ambient",
    ]

    conf_rand_action.add_argument(
        "-o",
        "--option",
        help="Option/Argument to be configured",
        choices=conf_rand_arguments,
    )

    conf_rand_action.set_defaults(validate=validate_randomizer_options)

    conf_rand_action.set_defaults(
        func=lambda args: handle_configure_randomizer(args, conf_rand_arguments)
    )


def validate_randomizer_options(args):
    """Check if asset key was supplied for some options (options for disk errors)"""

    if args["option"] and args["option"] != "ambient" and not args["asset_key"]:
        raise argparse.ArgumentTypeError(
            'Asset key is required for "{option}" option!'.format(**args)
        )


def handle_configure_randomizer(args, conf_rand_arguments):
    """Callback for CLI command for configuring randomizer"""

    # list all the randoptions
    if args["list"]:
        amb_props = ISystemEnvironment.get_ambient_props()

        print(
            "Ambient random arguments: range from {start} to {end}".format(**amb_props)
        )

        if not args["asset_key"]:
            return

        del conf_rand_arguments[conf_rand_arguments.index("ambient")]

        server_manager = get_server_state_manager(args["asset_key"])
        print("Server:[{0.key}] random arguments:".format(server_manager))
        for rand_opt in conf_rand_arguments:

            s_prop = IBMCServerStateManager.StorageRandProps[rand_opt.replace("-", "_")]
            opt_prop = server_manager.get_storage_radnomizer_prop(s_prop)
            print(
                " -- {}: range from {} to {}".format(rand_opt, opt_prop[0], opt_prop[1])
            )
        return

    # configure randargs - validate cli options
    if not args["start"] or not args["end"] or not args["option"]:
        raise argparse.ArgumentTypeError(
            "Must provide rand option, start & end range values!"
        )

    # update ambient option
    if args["option"] == "ambient":
        ISystemEnvironment.set_ambient_props(args)
        return

    # update one of the server disk options
    server_manager = get_server_state_manager(args["asset_key"])
    server_manager.set_storage_randomizer_prop(
        IBMCServerStateManager.StorageRandProps[args["option"].replace("-", "_")],
        slice(args["start"], args["end"]),
    )


def get_server_state_manager(asset_key):
    """Get server asset by key with type validation"""

    server_manager = IStateManager.get_state_manager_by_key(asset_key)
    if not isinstance(server_manager, IBMCServerStateManager):
        raise argparse.ArgumentTypeError(
            "Asset [{}] is not a server!".format(asset_key)
        )
    return server_manager


def configure_battery(key, kwargs):
    """Udpate runtime battery status"""

    state_manager = IStateManager.get_state_manager_by_key(key)

    if not isinstance(state_manager, IUPSStateManager):
        raise argparse.ArgumentTypeError("Asset [{}] is not a ups!".format(key))

    if kwargs["drain_speed"] is None and kwargs["charge_speed"] is None:
        raise argparse.ArgumentTypeError(
            'Must provide "--drain-speed" or "--charge-speed"'
        )

    if kwargs["drain_speed"] is not None:
        state_manager.set_drain_speed_factor(kwargs["drain_speed"])
    if kwargs["charge_speed"] is not None:
        state_manager.set_charge_speed_factor(kwargs["charge_speed"])
