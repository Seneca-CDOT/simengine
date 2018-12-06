"""Power management commands for assets and the system in general"""

from enginecore.state.state_managers import StateManager
from enginecore.state.assets import Asset


def power_command(power_group):
    """CLI endpoints for managing assets' power states & wallpower"""
    power_subp = power_group.add_subparsers()
    
    power_up_action = power_subp.add_parser('up', help="Power up a particular component/asset")
    power_up_action.add_argument('-k', '--asset-key', type=int, required=True)

    power_down_action = power_subp.add_parser('down', help="Power down a particular component/asset")
    power_down_action.add_argument('-k', '--asset-key', type=int, required=True)
    power_down_action.add_argument(
        '--hard', 
        help="Enable abrupt poweroff instead of shutdown",
        dest='hard', 
        action='store_true'
    )

    power_outage_action = power_subp.add_parser('outage', help="Simulate complete power loss")
    power_restore_action = power_subp.add_parser('restore', help="Restore mains power after outage")
    power_outage_action.set_defaults(func=lambda _: StateManager.power_outage())
    power_restore_action.set_defaults(func=lambda _: StateManager.power_restore())
    power_up_action.set_defaults(
        func=lambda args: manage_state(args['asset_key'], lambda a: a.power_up())
    )
    power_down_action.set_defaults(
        hard=False,
        func=lambda args: manage_state(args['asset_key'], lambda a: a.power_off() if args['hard'] else a.shut_down())
    )


def manage_state(asset_key, mng_action):
    """ Perform action for a node/asset with a certain key
    Args:
        asset_key (int): supplied asset identifier
        mng_action (func): callable object (lambda/function etc) that identifies action
    """
    state_manager = Asset.get_state_manager_by_key(asset_key, notify=True)
    mng_action(state_manager)
    