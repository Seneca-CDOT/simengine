"""Power management commands for assets and the system in general"""

from enginecore.state.net.state_client import StateClient
from enginecore.state.api import ISystemEnvironment


def power_command(power_group):
    """CLI endpoints for managing assets' power states & wallpower"""
    power_subp = power_group.add_subparsers()

    # Manage power of individual assets
    power_up_action = power_subp.add_parser(
        "up", help="Power up a particular component/asset"
    )
    power_up_action.add_argument("-k", "--asset-key", type=int, required=True)

    power_down_action = power_subp.add_parser(
        "down", help="Power down a particular component/asset"
    )
    power_down_action.add_argument("-k", "--asset-key", type=int, required=True)
    power_down_action.add_argument(
        "--hard",
        help="Enable abrupt poweroff instead of shutdown",
        dest="hard",
        action="store_true",
    )

    # Wallpower management
    power_outage_action = power_subp.add_parser(
        "outage", help="Simulate complete power loss"
    )
    power_restore_action = power_subp.add_parser(
        "restore", help="Restore mains power after outage"
    )

    # Voltage system-wide
    voltage_action_group = power_subp.add_parser(
        "voltage", help="Manage systems voltage behavior"
    )

    voltage_subp = voltage_action_group.add_subparsers()

    get_voltage_action = voltage_subp.add_parser(
        "get", help="Query current voltage configurations"
    )
    get_voltage_action.add_argument(
        "--value-only",
        help="Return voltage value only (omit details of voltage behaviour)",
        action="store_true",
    )

    set_voltage_action = voltage_subp.add_parser(
        "set", help="Update voltage value/voltage settings"
    )

    set_voltage_action.add_argument(
        "--value", type=float, help="Update voltage value (in Volts)"
    )

    set_voltage_action.add_argument(
        "--mu",
        type=float,
        help="Mean for gaussian random method for voltage fluctuations",
    )

    set_voltage_action.add_argument(
        "--sigma",
        type=float,
        help="Standard deviation for gaussian random method for voltage fluctuations",
    )

    set_voltage_action.add_argument(
        "--min",
        type=float,
        help="Min volt value for uniform random method for voltage fluctuations",
    )

    set_voltage_action.add_argument(
        "--max",
        type=float,
        help="Max volt value for uniform random method for voltage fluctuations",
    )

    set_voltage_action.add_argument(
        "--method",
        choices=ISystemEnvironment.voltage_random_methods(),
        help="Max volt value for uniform random method for voltage fluctuations",
    )

    set_voltage_action.add_argument(
        "--enable-fluctuation", dest="enabled", action="store_true"
    )
    set_voltage_action.add_argument(
        "--disable-fluctuation", dest="enabled", action="store_false"
    )

    # CLI action callbacks

    power_outage_action.set_defaults(func=lambda _: StateClient.power_outage())
    power_restore_action.set_defaults(func=lambda _: StateClient.power_restore())
    power_up_action.set_defaults(
        func=lambda args: manage_state(args["asset_key"], lambda a: a.power_up())
    )
    power_down_action.set_defaults(
        hard=False,  # abrupt shutdown if False by default
        func=lambda args: manage_state(
            args["asset_key"],
            lambda a: a.power_off() if args["hard"] else a.shut_down(),
        ),
    )

    set_voltage_action.set_defaults(func=handle_voltage_set)
    get_voltage_action.set_defaults(func=handle_voltage_get)


def handle_voltage_set(args):
    """Action callback for handling voltage set command"""
    if args["value"] is not None:
        StateClient.set_voltage(args["value"])

    del args["value"]

    # set voltage fluctuation properties if any are provided
    if [arg_value for _, arg_value in args.items() if arg_value is not None]:
        ISystemEnvironment.set_voltage_props(args)


def handle_voltage_get(args):
    """Action callback for handling voltage get command"""

    if args["value_only"]:
        print(ISystemEnvironment.get_voltage())
        return

    print("Voltage: {:.3f}V".format(ISystemEnvironment.get_voltage()))

    voltage_props = ISystemEnvironment.get_voltage_props()
    if not voltage_props:
        print("Voltage properties are not configured yet!")
        return

    volt_fluct_info = []

    volt_fluct_info.append("Fluctuation Properties:")
    volt_fluct_info.append("[enabled]: " + str(voltage_props["enabled"]))
    volt_fluct_info.append("[random distribution method]: " + voltage_props["method"])

    if voltage_props["method"] == "gauss":
        distr_prop_fmt = "mean({mu}), stdev({sigma})"
    else:
        distr_prop_fmt = "min({min}), max({max})"

    volt_fluct_info.append(
        "[distribution properties]: " + distr_prop_fmt.format(**voltage_props)
    )

    print("\n -> ".join(volt_fluct_info))


def manage_state(asset_key, mng_action):
    """Perform action for a node/asset with a certain key
    Args:
        asset_key (int): supplied asset identifier
        mng_action (func): callable object (lambda/function etc) that identifies action
    """
    state_manager = StateClient(asset_key)
    mng_action(state_manager)
