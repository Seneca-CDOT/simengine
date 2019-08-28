"""Creational tools for Model/System topology"""

import argparse
import enginecore.model.system_modeler as sys_modeler
from enginecore.state.api import ISystemEnvironment


def handle_link(kwargs):
    """Power connections"""
    link_action = (
        sys_modeler.remove_link if kwargs["remove"] else sys_modeler.link_assets
    )
    link_action(kwargs["source_key"], kwargs["dest_key"])


############# Validations


def validate_key(key):
    """Validate asset key"""
    if key > 9999 or key <= 0:
        raise argparse.ArgumentTypeError(
            "asset-key must be less than 9999 and greater than 0"
        )


def validate_server(kwargs):
    """Server-specific validation"""
    if kwargs["psu_num"] > 1 and (
        not kwargs["psu_load"] or len(kwargs["psu_load"]) != kwargs["psu_num"]
    ):
        raise argparse.ArgumentTypeError(
            "psu-load is required for server(-bmc) type when there're multiple PSUs"
        )


def model_command(asset_group):
    """Aggregates system modelling cli commands"""

    model_subp = asset_group.add_subparsers()

    # creational cmds
    create_command(model_subp.add_parser("create", help="Create new asset"))
    update_command(model_subp.add_parser("update", help="Update Asset properties"))

    ## MISC model commands
    reload_asset_action = model_subp.add_parser(
        "reload", help="Reload the system topology (notify daemon of model changes)"
    )

    # detach & delete an asset by key
    delete_asset_action = model_subp.add_parser(
        "delete", help="Remove individual asset by key"
    )
    delete_asset_action.add_argument("-k", "--asset-key", type=int, required=True)

    # drop entire system topology
    drop_system_action = model_subp.add_parser(
        "drop", help="Delete/drop all the system components"
    )

    # link 2 assets together
    power_asset_action = model_subp.add_parser(
        "power-link", help="Create/Delete a power link between 2 assets"
    )
    power_asset_action.add_argument(
        "-s",
        "--source-key",
        type=int,
        required=True,
        help="Key of an asset that POWERS dest. asset",
    )
    power_asset_action.add_argument(
        "-d",
        "--dest-key",
        type=int,
        required=True,
        help="Key of the asset powered by the source-key",
    )

    power_asset_action.add_argument(
        "-r", "--remove", action="store_true", help="Delete power conneciton if exists"
    )

    reload_asset_action.set_defaults(
        func=lambda args: ISystemEnvironment.reload_model()
    )

    delete_asset_action.set_defaults(
        func=lambda args: sys_modeler.delete_asset(args["asset_key"])
    )

    power_asset_action.set_defaults(func=handle_link)

    drop_system_action.set_defaults(func=lambda args: sys_modeler.drop_model())


def get_ups_command_parent():
    """Aggregate ups arg options"""
    ups_parent = argparse.ArgumentParser(add_help=False)

    ups_parent.add_argument(
        "--full-recharge-time",
        type=float,
        help="""Update recharge time for UPS, time taken (hours)
        to recharge fully depleted battery""",
        dest="full_recharge_time",
    )

    ups_parent.add_argument(
        "--min-power-bat",
        type=int,
        help="""Minimum battery level required before
        UPS output is powered on (where 1=0.1 percent)""",
        dest="min_power_on_battery_level",
        choices=range(0, 1001),
        metavar="[0-1001]",
    )

    ups_parent.add_argument(
        "--power-capacity",
        type=int,
        help="Output power capacity of the UPS",
        dest="output_power_capacity",
        choices=range(1, 5000),
        metavar="[1-5000]",
    )

    ups_parent.add_argument(
        "--runtime-graph",
        help="""Sampled runtime graph for the UPS in .JSON key-value format
        { wattage1: minutes, wattage2: minutes }""",
        dest="runtime",
    )

    ups_parent.add_argument(
        "--momentary-event-time",
        help="""Time period (in seconds) before outage/brownout
        state is assigned in case of input power failure
        (waits "n" seconds after momentary cause for transfer reason)""",
        type=int,
    )

    ups_parent.add_argument(
        "--percent-of-rated-output",
        help="""Percentage (between 0 and 1) of nominal output voltage from the UPS
        in VAC which determines threshold for brownout vs blackout""",
        type=float,
        metavar="[0.0-1.0]",
    )

    return ups_parent


def update_command(update_asset_group):
    """Update existing asset"""

    update_actions = []

    update_asset_parent = argparse.ArgumentParser(add_help=False)
    update_asset_parent.add_argument(
        "-k",
        "--asset-key",
        type=int,
        required=True,
        help="Key of the asset to be updated",
    )
    update_asset_parent.add_argument(
        "--on-delay", type=int, help="Power on delay in ms"
    )
    update_asset_parent.add_argument(
        "--off-delay", type=int, help="Power on delay in ms"
    )

    update_asset_parent.add_argument(
        "-x", type=int, help="x - asset position on the dashboard"
    )
    update_asset_parent.add_argument(
        "-y", type=int, help="y - asset position on the dashboard"
    )
    update_asset_parent.add_argument("-n", "--name", help="Name displayed on the UI")
    update_asset_parent.add_argument(
        "--power-on-ac",
        dest="power_on_ac",
        action="store_true",
        help="Power up on AC restored",
    )
    update_asset_parent.add_argument(
        "--no-power-on-ac",
        dest="power_on_ac",
        action="store_false",
        help="Don't power up when AC is restored",
    )
    update_volt_parent = argparse.ArgumentParser(add_help=False)
    update_volt_parent.add_argument(
        "--min-voltage",
        type=float,
        help="Voltage value below/at which asset stops functioning",
    )

    # snmp group parent will contain snmp-specific args
    update_snmp_parent = argparse.ArgumentParser(add_help=False)
    update_snmp_parent.add_argument("--host", type=str, help="SNMP interface host")
    update_snmp_parent.add_argument("--port", type=int, help="SNMP interface port")

    # server group
    update_server_parent = argparse.ArgumentParser(add_help=False)
    update_server_parent.add_argument(
        "--domain-name", help="VM domain name", required=True
    )

    # power consuming assets group
    update_power_parent = argparse.ArgumentParser(add_help=False)
    update_power_parent.add_argument("--power-source", type=int)
    update_power_parent.add_argument(
        "--power-consumption", type=int, help="Power consumption in Watts"
    )

    update_subp = update_asset_group.add_subparsers()

    ## OUTLET
    update_outlet_action = update_subp.add_parser(
        "outlet", help="Update outlet properties", parents=[update_asset_parent]
    )

    ## PDU
    update_pdu_action = update_subp.add_parser(
        "pdu",
        help="Update PDU properties",
        parents=[update_asset_parent, update_volt_parent, update_snmp_parent],
    )

    ## UPS
    update_ups_action = update_subp.add_parser(
        "ups",
        help="Update UPS properties",
        parents=[
            update_asset_parent,
            update_volt_parent,
            update_snmp_parent,
            get_ups_command_parent(),
        ],
    )

    ## Server
    update_server_action = update_subp.add_parser(
        "server",
        help="Update Server properties",
        parents=[
            update_asset_parent,
            update_volt_parent,
            update_server_parent,
            update_power_parent,
        ],
    )

    ## Server BMC
    update_server_bmc_action = update_subp.add_parser(
        "server-bmc",
        help="Update Server-With BMC properties",
        parents=[
            update_asset_parent,
            update_volt_parent,
            update_server_parent,
            update_power_parent,
        ],
    )

    update_server_bmc_action.add_argument(
        "--user", type=str, help="BMC-enabled server: IPMI admin user"
    )
    update_server_bmc_action.add_argument(
        "--password", type=str, help="BMC-enabled server: IPMI user password"
    )
    update_server_bmc_action.add_argument(
        "--port", type=int, help="IPMI interface port"
    )
    update_server_bmc_action.add_argument(
        "--vmport",
        type=int,
        help="IPMI serial VM interface for channel 15 (the system interface)",
    )

    ## Static
    update_static_action = update_subp.add_parser(
        "static",
        help="Update Static Asset properties",
        parents=[update_asset_parent, update_volt_parent, update_power_parent],
    )

    update_static_action.add_argument(
        "--img-url", help="URL of the image displayed on the frontend"
    )

    ## Lamp
    update_lamp_action = update_subp.add_parser(
        "lamp",
        help="Update lamp Asset properties",
        parents=[update_asset_parent, update_volt_parent, update_power_parent],
    )

    update_actions.extend(
        [
            update_outlet_action,
            update_pdu_action,
            update_ups_action,
            update_server_action,
            update_server_bmc_action,
            update_static_action,
            update_lamp_action,
        ]
    )

    for action in update_actions:
        action.set_defaults(
            func=lambda args: sys_modeler.configure_asset(args["asset_key"], args)
        )


def create_command(create_asset_group):
    """Model creation (cli endpoints to initialize system topology) """

    # parent will contain args shared by all the asset types
    # (such as key, [x,y] positions, name etc.)
    create_asset_parent = argparse.ArgumentParser(add_help=False)
    create_asset_parent.add_argument(
        "-k",
        "--asset-key",
        type=int,
        required=True,
        help="Unique asset key (must be <= 9999)",
    )
    create_asset_parent.add_argument(
        "--on-delay", type=int, help="Power on delay in ms", default=0
    )

    create_asset_parent.add_argument(
        "--off-delay", type=int, help="Power on delay in ms", default=0
    )

    create_asset_parent.add_argument(
        "-x", type=int, help="x - asset position on the dashboard", default=0
    )
    create_asset_parent.add_argument(
        "-y", type=int, help="y - asset position on the dashboard", default=0
    )

    create_asset_parent.add_argument(
        "--power-on-ac",
        dest="power_on_ac",
        action="store_true",
        help="Power up on AC restored",
    )
    create_asset_parent.add_argument(
        "--no-power-on-ac",
        dest="power_on_ac",
        action="store_false",
        help="Don't power up when AC is restored",
    )

    create_asset_parent.add_argument("-n", "--name", help="Name displayed on the UI")
    create_asset_parent.set_defaults(new_asset=True, power_on_ac=True)

    create_volt_parent = argparse.ArgumentParser(add_help=False)
    create_volt_parent.add_argument(
        "--min-voltage",
        type=float,
        help="Voltage value below/at which asset stops functioning",
        default=90.0,
    )

    # snmp group parent will contain snmp-specific args
    create_snmp_parent = argparse.ArgumentParser(add_help=False)
    create_snmp_parent.add_argument(
        "--host", type=str, default="localhost", help="SNMP interface host"
    )
    create_snmp_parent.add_argument(
        "--port", type=int, required=True, help="SNMP interface port"
    )
    create_snmp_parent.add_argument(
        "--snmp-preset", type=str, help="Vendor-specific asset configurations"
    )

    create_snmp_parent.add_argument(
        "--serial-number", type=str, help="Serial number of a simulated SNMP device"
    )

    create_snmp_parent.add_argument(
        "--mac-address", type=str, help="MAC address of a simulated SNMP device"
    )

    create_snmp_parent.add_argument(
        "--interface", type=str, help="Network interface attached to SNMP device"
    )

    create_snmp_parent.add_argument("--mask", type=str, help="Net mask of interface")

    # server group
    create_server_parent = argparse.ArgumentParser(add_help=False)
    create_server_parent.add_argument("--domain-name", help="VM domain name")

    # power consuming assets group
    create_power_parent = argparse.ArgumentParser(add_help=False)
    create_power_parent.add_argument(
        "--power-source", type=int, default=ISystemEnvironment.wallpower_volt_standard()
    )
    create_power_parent.add_argument(
        "--power-consumption",
        required=True,
        type=int,
        help="Power consumption in Watts",
    )

    ## > Add type-specific args < ##

    create_subp = create_asset_group.add_subparsers()

    ## OUTLET
    create_outlet_action = create_subp.add_parser(
        "outlet", help="Create a Simple outlet asset", parents=[create_asset_parent]
    )

    ## PDU
    create_pdu_action = create_subp.add_parser(
        "pdu",
        help="Create PDU asset",
        parents=[create_asset_parent, create_volt_parent, create_snmp_parent],
    )

    ## UPS
    create_ups_action = create_subp.add_parser(
        "ups",
        help="Create UPS asset",
        parents=[create_asset_parent, create_snmp_parent, get_ups_command_parent()],
    )

    create_ups_action.add_argument(
        "--power-source",
        help="Asset Voltage",
        type=int,
        default=ISystemEnvironment.wallpower_volt_standard(),
    )
    create_ups_action.add_argument(
        "--power-consumption",
        type=int,
        help="""Power consumption in Watts
          (how much UPS draws when not powering anything)""",
        default=24,
    )

    ## SERVER
    create_server_action = create_subp.add_parser(
        "server",
        help="Create a server asset (VM)",
        parents=[
            create_asset_parent,
            create_volt_parent,
            create_server_parent,
            create_power_parent,
        ],
    )

    create_server_action.add_argument(
        "--psu-num", type=int, default=1, help="Number of PSUs installed in the server"
    )
    create_server_action.add_argument(
        "--psu-load",
        nargs="+",
        type=float,
        help="""PSU(s) load distribution (the downstream power is multiplied
        by the value, e.g.  for 2 PSUs if '--psu-load 0.5 0.5',
        load is divided equally) \n""",
    )

    create_server_action.add_argument(
        "--psu-power-consumption",
        nargs="+",
        type=int,
        default=6,
        help="""Power consumption of idle PSU \n""",
    )

    create_server_action.add_argument(
        "--psu-power-source",
        nargs="+",
        type=int,
        default=ISystemEnvironment.wallpower_volt_standard(),
        help="""PSU Voltage \n""",
    )

    ## SERVER-BMC
    create_server_bmc_action = create_subp.add_parser(
        "server-bmc",
        help="Create a server asset (VM) that supports IPMI interface",
        parents=[
            create_asset_parent,
            create_volt_parent,
            create_server_parent,
            create_power_parent,
        ],
    )

    create_server_bmc_action.add_argument(
        "--user",
        type=str,
        default="ipmiusr",
        help="BMC-enabled server: IPMI admin user",
    )
    create_server_bmc_action.add_argument(
        "--password",
        type=str,
        default="test",
        help="BMC-enabled server: IPMI user password",
    )
    create_server_bmc_action.add_argument(
        "--host", type=str, default="localhost", help="IPMI interface host"
    )
    create_server_bmc_action.add_argument(
        "--port", type=int, default=9001, help="IPMI interface port"
    )

    create_server_bmc_action.add_argument(
        "--interface",
        type=str,
        default="",
        help="Network interface attached to the server",
    )
    create_server_bmc_action.add_argument(
        "--vmport",
        type=int,
        default=9002,
        help="IPMI serial VM interface for channel 15 (the system interface)",
    )

    create_server_bmc_action.add_argument(
        "--storcli-port",
        type=int,
        default=50000,
        help="Storcli websocket port used to establish a connection with a vm",
    )

    create_server_bmc_action.add_argument(
        "--sensor-def",
        type=str,
        help="""File containing sensor definitions 
        (defaults to sensors.json file in enginecore/enginecore/model/presets)""",
    )

    create_server_bmc_action.add_argument(
        "--storage-def",
        type=str,
        help="""File containing storage definitions 
        (defaults to storage.json file in enginecore/enginecore/model/presets)
        """,
    )

    create_server_bmc_action.add_argument(
        "--storage-states",
        type=str,
        help="""File containing storage state mappings (.JSON)
        """,
    )

    ## STATIC
    create_static_action = create_subp.add_parser(
        "static",
        help="Add static (dummy) asset",
        parents=[create_asset_parent, create_volt_parent, create_power_parent],
    )

    create_static_action.add_argument(
        "--img-url", help="URL of the image displayed on the frontend"
    )

    ## LAMP
    create_lamp_action = create_subp.add_parser(
        "lamp",
        help="Used for power demonstrations",
        parents=[create_asset_parent, create_volt_parent, create_power_parent],
    )

    create_outlet_action.set_defaults(
        validate=lambda args: validate_key(args["asset_key"]),
        func=lambda args: sys_modeler.create_outlet(args["asset_key"], args),
    )

    create_pdu_action.set_defaults(
        validate=lambda args: validate_key(args["asset_key"]),
        func=lambda args: sys_modeler.create_pdu(args["asset_key"], args),
    )

    create_ups_action.set_defaults(
        validate=lambda args: validate_key(args["asset_key"]),
        func=lambda args: sys_modeler.create_ups(args["asset_key"], args),
    )

    create_server_action.set_defaults(
        validate=lambda args: [validate_key(args["asset_key"]), validate_server(args)],
        func=lambda args: sys_modeler.create_server(args["asset_key"], args),
    )

    create_server_bmc_action.set_defaults(
        validate=lambda args: [validate_key(args["asset_key"])],
        func=lambda args: sys_modeler.create_server(
            args["asset_key"],
            args,
            server_variation=sys_modeler.ServerVariations.ServerWithBMC,
        ),
    )

    create_static_action.set_defaults(
        validate=lambda args: validate_key(args["asset_key"]),
        func=lambda args: sys_modeler.create_static(args["asset_key"], args),
    )

    create_lamp_action.set_defaults(
        validate=lambda args: validate_key(args["asset_key"]),
        func=lambda args: sys_modeler.create_lamp(args["asset_key"], args),
    )
