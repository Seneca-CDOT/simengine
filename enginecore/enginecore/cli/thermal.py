"""Thermal/Temperature related functionalities:
- ambient management
- thermal commands for server assets that support IPMI/BMC 
"""

import argparse
import enginecore.model.system_modeler as sys_modeler
from enginecore.state.api import ISystemEnvironment, IBMCServerStateManager
from enginecore.state.sensor.repository import SensorRepository
from enginecore.state.net.state_client import StateClient

from enginecore.cli.storage import get_ctrl_storage_args


def thermal_command(thermal_group):
    """Manage thermal with 3 endpoint commands"""

    thermal_subp = thermal_group.add_subparsers()

    ambient_command(
        thermal_subp.add_parser(
            "ambient",
            help="Configure/Retrieve ambient state (room temperature settings)",
        )
    )

    cpu_usage_command(
        thermal_subp.add_parser(
            "cpu-usage",
            help="Configure relationships between CPU load and server sensors",
        )
    )

    sensor_command(
        thermal_subp.add_parser(
            "sensor", help="Configure/Retrieve sensor state and relationships"
        )
    )

    storage_command(
        thermal_subp.add_parser(
            "storage",
            help="Configure/Retrieve thermal relationship \
                between sensors & storage elements",
        )
    )


def ambient_command(th_ambient_group):
    """Aggregate ambient CLI options"""

    th_ambient_subp = th_ambient_group.add_subparsers()

    th_get_ambient_action = th_ambient_subp.add_parser(
        "get", help="Query current thermal configurations"
    )
    th_get_ambient_action.add_argument(
        "--value-only", help="Return ambient value only", action="store_true"
    )

    th_set_ambient_action = th_ambient_subp.add_parser(
        "set", help="Update ambient thermal settings"
    )

    th_set_ambient_action.add_argument(
        "-d",
        "--degrees",
        type=float,
        help="Update ambient temperature (in Celsius); \
            if time period and event are specified, \
            this value will be added to the previous room temp;",
        required=True,
    )

    th_set_ambient_action.add_argument(
        "-e",
        "--event",
        help="Increase/Descrease temperature on down/up mains event",
        choices=["up", "down"],
    )

    th_set_ambient_action.add_argument(
        "-p",
        "--pause-at",
        help="Increase/Descrease room temperature until this value is reached",
        type=float,
    )

    th_set_ambient_action.add_argument(
        "-r", "--rate", type=int, help="Update temperature value very 'n' seconds"
    )

    # set-up callbacks for the commands
    th_get_ambient_action.set_defaults(func=handle_get_thermal_ambient)
    th_set_ambient_action.set_defaults(func=handle_set_thermal_ambient)


def cpu_usage_command(th_cpu_usg_group):
    """CLI endpoints for handling CPU usage and sensor relationships"""

    th_cpu_usg_subp = th_cpu_usg_group.add_subparsers()

    # - SET

    th_set_cpu_usg_action = th_cpu_usg_subp.add_parser(
        "set", help="Update CPU usage / sensor relationship"
    )

    th_set_cpu_usg_action.add_argument(
        "-k",
        "--asset-key",
        help="Key of the server sensor belongs to ",
        type=int,
        required=True,
    )

    th_set_cpu_usg_action.add_argument(
        "-t",
        "--target-sensor",
        help="Name of the target sensor affected by CPU load",
        type=str,
        required=True,
    )

    th_set_cpu_usg_action.add_argument(
        "-m",
        "--model",
        help=".JSON model representing CPU usage &\
            corresponding thermal change for the sensor value",
        type=str,
        required=True,
    )

    # - GET
    th_get_cpu_usg_action = th_cpu_usg_subp.add_parser(
        "get", help="Retrieve configured CPU usage / sensor relationship"
    )

    th_get_cpu_usg_action.add_argument(
        "-k",
        "--asset-key",
        help="Key of the server sensors belong to ",
        type=int,
        required=True,
    )

    # - DELETE

    th_delete_cpu_usg_action = th_cpu_usg_subp.add_parser(
        "delete", help="Delete existing CPU usage / sensor relationship"
    )

    th_delete_cpu_usg_action.add_argument(
        "-k",
        "--asset-key",
        help="Key of the server sensors belong to ",
        type=int,
        required=True,
    )

    th_delete_cpu_usg_action.add_argument(
        "-t",
        "--target-sensor",
        help="Name of the target sensor affected by CPU load",
        type=str,
        required=True,
    )

    th_get_cpu_usg_action.set_defaults(func=handle_get_thermal_cpu)

    th_set_cpu_usg_action.set_defaults(
        func=IBMCServerStateManager.update_thermal_cpu_target
    )

    th_delete_cpu_usg_action.set_defaults(func=sys_modeler.delete_thermal_cpu_target)


def get_thermal_add_args():
    # group a few args into a common parent element
    thermal_parent = argparse.ArgumentParser(add_help=False)

    thermal_parent.add_argument(
        "-s",
        "--source-sensor",
        help="Name of the source sensor",
        type=str,
        required=True,
    )

    thermal_parent.add_argument(
        "-e",
        "--event",
        help="Event associated with the source sensor",
        choices=["up", "down"],
    )

    thermal_parent.add_argument(
        "-a",
        "--action",
        help="Action associated with the event \
            (for instance, on sensor 0x1 going down, \
            the target sensor value will be either increased or decreased)\
            Action can be omitted and in this case: \
            'increase' action will be assigned to 'down' event & \
            'decrese' action will be assigned to 'up' event ",
        choices=["increase", "decrease"],
    )

    thermal_parent.add_argument(
        "--model",
        "-m",
        help="Simengine will use this .JSON model to determine \
            thermal impact for any given source sensor input; \
            Source sensor's default value will be used instead if not specified",
    )

    thermal_parent.add_argument(
        "-d",
        "--degrees",
        type=float,
        help="Update sensor temperature (in Celsius); \
            if time period and event are specified, \
            this value will be added to the previous sensor temp;",
    )

    thermal_parent.add_argument(
        "-p",
        "--pause-at",
        help="Increase/Descrease room temperature until this value is reached",
        type=float,
        required=True,
    )

    thermal_parent.add_argument(
        "-r",
        "--rate",
        help="Update temperature value very 'n' seconds",
        type=int,
        required=True,
    )

    return thermal_parent


def storage_command(th_storage_group):
    """configure thermal props of storage componenets"""
    th_storage_subp = th_storage_group.add_subparsers()

    # Add new relationship:
    th_set_storage_action = th_storage_subp.add_parser(
        "set",
        help="Update storage thermal settings",
        parents=[get_ctrl_storage_args(), get_thermal_add_args()],
    )

    th_set_storage_action.add_argument(
        "--drive", help="DID of the physical drive this sensor is affecting", type=str
    )

    th_set_storage_action.add_argument(
        "--cache-vault",
        help="Serial number of CacheVault sensor is affecting",
        type=str,
    )

    th_set_storage_action.set_defaults(
        validate=lambda attr: attr["drive"] or attr["cache_vault"],
        func=handle_set_thermal_storage,
    )

    # Delete existing:

    th_delete_storage_action = th_storage_subp.add_parser(
        "delete",
        help="Delete thermal connection between a sensor \
            and a storage component (cv or physical drive)",
    )

    th_delete_storage_action.add_argument(
        "-k",
        "--asset-key",
        help="Key of the server sensor/storage component belongs to ",
        type=int,
        required=True,
    )
    th_delete_storage_action.add_argument(
        "-s",
        "--source-sensor",
        help="Name of the source sensor",
        type=str,
        required=True,
    )

    th_delete_storage_action.add_argument(
        "-c", "--controller", help="Controller number", type=int, required=True
    )

    th_delete_storage_action.add_argument(
        "--drive", help="DID of the physical drive this sensor is affecting", type=str
    )

    th_delete_storage_action.add_argument(
        "--cache-vault",
        help="Serial number of CacheVault sensor is affecting",
        type=str,
    )

    th_delete_storage_action.add_argument(
        "-e",
        "--event",
        help="Event associated with the source sensor",
        choices=["up", "down"],
        required=True,
    )

    th_delete_storage_action.set_defaults(
        func=IBMCServerStateManager.delete_thermal_storage_target
    )


def sensor_command(th_sensor_group):
    """Sensor related thermal commands (listing all, configuring etc...)"""

    th_sensor_subp = th_sensor_group.add_subparsers()

    # - SET

    th_set_sensor_action = th_sensor_subp.add_parser(
        "set", help="Update sensor thermal settings", parents=[get_thermal_add_args()]
    )

    th_set_sensor_action.add_argument(
        "-k",
        "--asset-key",
        help="Key of the server sensors belong to ",
        type=int,
        required=True,
    )

    th_set_sensor_action.add_argument(
        "-t",
        "--target-sensor",
        help="Name of the target sensor affected by the event \
            associated with the source sensor",
        type=str,
        required=True,
    )

    # - GET

    th_get_sensor_action = th_sensor_subp.add_parser(
        "get",
        help="""
        Query current thermal configurations for all the sensors or a specific sensor
        (if sensor name is provided)
        """,
    )

    th_get_sensor_action.add_argument(
        "-k",
        "--asset-key",
        help="Key of the server sensor belongs to ",
        type=int,
        required=True,
    )

    th_get_sensor_action.add_argument(
        "-s", "--sensor", help="Name of the sensor", type=str
    )

    # - DELETE

    th_delete_sensor_action = th_sensor_subp.add_parser(
        "delete", help="Delete thermal connection between 2 sensors"
    )

    th_delete_sensor_action.add_argument(
        "-k",
        "--asset-key",
        help="Key of the server sensor belongs to ",
        type=int,
        required=True,
    )
    th_delete_sensor_action.add_argument(
        "-s",
        "--source-sensor",
        help="Name of the source sensor",
        type=str,
        required=True,
    )
    th_delete_sensor_action.add_argument(
        "-t",
        "--target-sensor",
        help="Name of the target sensor affected by the event \
            associated with the source sensor",
        type=str,
        required=True,
    )
    th_delete_sensor_action.add_argument(
        "-e",
        "--event",
        help="Event associated with the source sensor",
        choices=["up", "down"],
        required=True,
    )

    # set-up callbacks for the commands
    th_get_sensor_action.set_defaults(func=handle_get_thermal_sensor)
    th_set_sensor_action.set_defaults(func=handle_set_thermal_sensor)
    th_delete_sensor_action.set_defaults(
        func=sys_modeler.delete_thermal_sensor_target  # TODO: change sys_modeler to IBMCServerStateManager
    )


def handle_get_thermal_cpu(kwargs):
    """Display current cpu & sensor relationship"""

    th_cpu_details = IBMCServerStateManager.get_thermal_cpu_details(kwargs["asset_key"])

    if not th_cpu_details:
        print(
            "There are no cpu/sensor relationships for server {}".format(
                kwargs["asset_key"]
            )
        )
    else:
        th_cpu_fmt = lambda x: " --> t:[{}] using model '{}'".format(
            x["sensor"]["name"], x["rel"]["model"]
        )
        print(
            "\n".join(
                ["Server [{}]:".format(kwargs["asset_key"])]
                + list(map(th_cpu_fmt, th_cpu_details))
            )
        )


def handle_set_thermal_ambient(kwargs):
    """Configure thermal properties for room temperature"""

    if kwargs["event"] and kwargs["pause_at"] and kwargs["rate"]:
        ISystemEnvironment.set_ambient_props(kwargs)
    elif kwargs["event"] or kwargs["pause_at"] or kwargs["rate"]:
        raise argparse.ArgumentTypeError("Event, pause-at and rate must be supplied")
    else:
        StateClient.set_ambient(kwargs["degrees"])


def handle_get_thermal_ambient(kwargs):
    """Print some general information about ambient configurations"""

    if kwargs["value_only"]:
        print(ISystemEnvironment.get_ambient())
    else:
        print("Ambient: {}° ".format(ISystemEnvironment.get_ambient()))

        ambient_props = ISystemEnvironment.get_ambient_props()
        if not ambient_props:
            print("Ambient event properties are not configured yet!")
            return

        prop_fmt = "{degrees}°/{rate} sec, until {pauseAt}° is reached"
        print("AC settings:")
        print(" -> [online]  : decrease by " + prop_fmt.format(**ambient_props["up"]))
        print(" -> [offline] : increase by " + prop_fmt.format(**ambient_props["down"]))


def handle_set_thermal_sensor(kwargs):
    """Configure thermal sensor relations & properties"""

    if not kwargs["action"] and kwargs["event"]:
        kwargs["action"] = "increase" if kwargs["event"] == "down" else "decrease"
    elif not kwargs["action"] and kwargs["model"]:
        raise argparse.ArgumentTypeError(
            "Must provide action type (increase/decrease) when model is specified"
        )

    if not kwargs["degrees"] and not kwargs["model"]:
        raise argparse.ArgumentTypeError(
            "Must provide either the model or constant degree value!"
        )

    if kwargs["model"]:
        kwargs["event"] = "up"

    IBMCServerStateManager.update_thermal_sensor_target(kwargs)


def handle_set_thermal_storage(kwargs):
    if not kwargs["cache_vault"] and not kwargs["drive"]:
        raise argparse.ArgumentTypeError(
            "Must provide either target drive id or cachevault!"
        )

    IBMCServerStateManager.update_thermal_storage_target(kwargs)


def handle_get_thermal_sensor(kwargs):
    """Display information about BMC sensors"""
    if kwargs["sensor"]:
        print(
            SensorRepository(kwargs["asset_key"]).get_sensor_by_name(kwargs["sensor"])
        )
    else:
        print(SensorRepository(kwargs["asset_key"]))
