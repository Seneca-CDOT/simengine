"""MISC: exposes various system's state props configurations """

import argparse
from enginecore.state.assets import Asset
from enginecore.state.sensors import SensorRepository

def configure_command(configure_state_group):
    """Update some runtime values of the system components"""

    conf_state_subp = configure_state_group.add_subparsers()
    conf_ups_action = conf_state_subp.add_parser('ups', help="Update UPS runtime properties")
    conf_ups_action.add_argument(
        '-k', '--asset-key', type=int, required=True, help="Unique asset key of the UPS"
    )

    conf_ups_action.add_argument(
        '-d', '--drain-speed', type=float, help="Update factor of the battery drain (1 sets to regular speed)", 
        choices=range(1, 101), 
        metavar="[1-101]"
    )

    conf_ups_action.add_argument(
        '-c', '--charge-speed', type=float, help="Update factor of the battery charge (1 sets to regular speed)", 
        choices=range(1, 101), 
        metavar="[1-101]"
    )

    conf_sensor_action = conf_state_subp.add_parser('sensor', help="Update sensor runtime properties")
    conf_sensor_action.add_argument(
        '-k', '--asset-key', type=int, required=True, help="Unique asset key of the server sensor belongs to"
    )

    conf_sensor_action.add_argument(
        '-s', '--sensor-name', type=str, required=True, help="Name of the sensor"
    )

    conf_sensor_action.add_argument(
        '-r', '--runtime-value', required=True, help="New sensor value (will be reflected on ipmi)"
    )

    conf_ups_action.set_defaults(func=lambda args: configure_battery(args['asset_key'], args))
    conf_sensor_action.set_defaults(func=configure_sensor)

    
def configure_battery(key, kwargs):
    """Udpate runtime battery status"""
    if kwargs['drain_speed'] is not None:
        state_manager = Asset.get_state_manager_by_key(key, notify=True)
        state_manager.set_drain_speed_factor(kwargs['drain_speed'])
    if kwargs['charge_speed'] is not None:
        state_manager = Asset.get_state_manager_by_key(key, notify=True)
        state_manager.set_charge_speed_factor(kwargs['charge_speed'])


def configure_sensor(kwargs):
    """Update runtime sensor value"""
    try:
        sensor = SensorRepository(kwargs['asset_key']).get_sensor_by_name(kwargs['sensor_name'])
        sensor.sensor_value = kwargs['runtime_value']
    except KeyError as error:
        raise argparse.ArgumentTypeError("Server or Sensor does not exist: " + str(error))
