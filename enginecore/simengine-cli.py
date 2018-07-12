#!/usr/bin/env python3
""" Command line interface for enginecore """
# pylint: disable=C0103

import argparse
import json
import time
import curses

from enginecore.state.assets import SUPPORTED_ASSETS
from enginecore.model.graph_reference import GraphReference
import enginecore.model.system_modeler as sm
from enginecore.state.state_managers import StateManger
from enginecore.state.utils import get_asset_type

ASSET_TYPES = ['pdu', 'outlet', 'server', 'server-bmc', 'static']

def manage_state(asset_key, action):
    """ Perform action for a node/asset with a certain key
    Args:
            asset_key (int): supplied asset identifier
            action (func): callable object (lambda/function etc) that identifies action
    """
    with GraphReference().get_session() as session:
        
        asset_info = GraphReference.get_asset_and_components(session, asset_key)
        
        asset_type = get_asset_type(asset_info['labels'])
        state_manager = SUPPORTED_ASSETS[asset_type].StateManagerCls(asset_info, notify=True)
        
        action(state_manager)

class bcolors:
    """ curses colours """
    OKGREEN = 2
    ERROR = 1


def status_table_format(assets, stdscr=False):
    """ Display status in a table format 
    Args:
            assets (dict): list of assets supported by the system
            stdscr (optional): default window return by initscr(), status_table_format uses print if omitted
    """
    
    # format headers
    headers = ["Asset Key", "Type", "Status", "Children", "Load"]
    row_format = "{:>10}" * (len(headers) + 1)

    headers = row_format.format("", *headers, end='')
    if stdscr: 
        stdscr.addstr(0, 0, headers)
    else:
        print(headers)

    for i, asset_key in enumerate(assets):
        asset = assets[asset_key]
        children = str(asset['children'] if 'children' in asset else "none")
        row = row_format.format(str(i), *[str(asset_key), asset['type'], str(asset['status']), children, "{0:.2f}".format(asset['load'])], end='')

        if stdscr:
            stdscr.addstr(i+1, 0, row, curses.color_pair(bcolors.ERROR if int(asset['status']) == 0 else bcolors.OKGREEN))
        else:
            print(row)

    if stdscr:
        stdscr.refresh()


def get_status(**kwargs):
    """ Retrieve power states of the assets 
    Args:
        **kwargs: Command line options
    """
    
    #### one asset ####
    if kwargs['asset_key'] and kwargs['load']:
        with GraphReference().get_session() as session:
            asset_info = GraphReference.get_asset_and_components(session, int(kwargs['asset_key']))
            asset_type = get_asset_type(asset_info['labels'])
            state_manager = SUPPORTED_ASSETS[asset_type].StateManagerCls(asset_info)
            print("{}-{} : {}".format(asset_info['key'], asset_type, state_manager.get_load()))
            return

    elif kwargs['asset_key']:
        asset = StateManger.get_asset_status(int(kwargs['asset_key']))
        print("{key}-{type} : {status}".format(**asset))
        return

    ##### list states #####
    assets = StateManger.get_system_status()

    # json format
    if kwargs['print_as'] == 'json': 
        print(json.dumps(assets, indent=4))

    # monitor state with curses
    elif kwargs['monitor']:
        stdscr = curses.initscr()

        curses.noecho()
        curses.cbreak()

        try:
            curses.start_color()
            curses.use_default_colors()
            for i in range(0, curses.COLORS):
                curses.init_pair(i, i, -1)
            while True:
                status_table_format(assets, stdscr)
                time.sleep(kwargs['watch_rate'])
                assets = StateManger.get_system_status()
        except KeyboardInterrupt:
            pass
        finally:
            curses.echo()
            curses.nocbreak()
            curses.endwin()
            
    # human-readable table
    else:
        status_table_format(assets)


def create_asset(**kwargs):
    """Add new asset to the system/model """

    asset_type = kwargs['asset_type']
    
    # validation not done by argparser
    if kwargs['asset_key'] > 9999:
        raise argparse.ArgumentTypeError("asset-key must be <= 9999")
    if (asset_type == 'server' or asset_type == 'server-bmc'):
        if kwargs['psu_num'] > 1 and (not kwargs['psu_load'] or len(kwargs['psu_load']) != kwargs['psu_num']):
            raise argparse.ArgumentTypeError("psu-load is required for server(-bmc) type when there're multiple PSUs")
        if not kwargs['domain_name']:
            raise argparse.ArgumentTypeError("domain-name is required for server(-bmc) type")
        if not kwargs['power_consumption']:
            raise argparse.ArgumentTypeError("power-consumption is required for server(-bmc) type")
            

    # attempt to add an asset to the system topology
    try:
        if asset_type == 'pdu':
            sm.create_pdu(kwargs['asset_key'], kwargs)
        elif asset_type == 'outlet':
            sm.create_outlet(kwargs['asset_key'], kwargs)
        elif asset_type == 'static':
            sm.create_static(kwargs['asset_key'], kwargs)
        elif asset_type == 'server':
            sm.create_server(kwargs['asset_key'], kwargs)
        elif asset_type == 'server-bmc':
            sm.create_server(kwargs['asset_key'], kwargs, server_variation='ServerWithBMC')
        else:
            print("The asset type must be either 'outlet', 'pdu' or 'static'")
    except KeyError as e:
        print(e)

################ Define Command line options & arguments

argparser = argparse.ArgumentParser(
    description='Simengine CLI provides a set of management tools for the engine core'
)
subparsers = argparser.add_subparsers()

power_group = subparsers.add_parser('power', help="Control power component of registered asset(s)")

## -> Setup options for state queries
status_group = subparsers.add_parser('status', help="Retrieve status of registered asset(s)")
status_group.add_argument('-k', '--asset-key', type=int)
status_group.add_argument('--print-as', help="Format options")
status_group.add_argument('--monitor', help="Monitor status", action='store_true')
status_group.add_argument('--load', help="Check load", action='store_true')

status_group.add_argument('--watch-rate', nargs='?', 
                          help="Update state every n seconds, defaults to 1", default=1, type=int)


## -> Setup options for oid queries
oid_group = subparsers.add_parser('oid', help="Manage OIDs")

## -> Setup options for snapshot commands
snapshot_group = subparsers.add_parser('snapshot', help="Manage snapshots of the assets' states")

## -> Setup options for asset management commands

asset_group = subparsers.add_parser('model', help="Manage system model: create new/update existing asset etc.")
subparsers = asset_group.add_subparsers()
create_asset_action = subparsers.add_parser('create', help="Create new asset")
create_asset_action.add_argument(
    '-k', '--asset-key', type=int, required=True, help="Unique asset key (must be <= 9999)"
    )
create_asset_action.add_argument(
    '-t', '--asset-type', required=True, help="Type of the machine/asset", choices=ASSET_TYPES
    )
create_asset_action.add_argument('--host')
create_asset_action.add_argument('--on-delay', type=int, help="Power on delay in ms", default=-1)
create_asset_action.add_argument('--off-delay', type=int, help="Power on delay in ms", default=-1)

# static asset options
create_asset_action.add_argument('--img-url')
create_asset_action.add_argument('--power-source', type=int, default=120)
create_asset_action.add_argument('--power-consumption', type=int, help="Power consumption in Watts")
create_asset_action.add_argument('--name')

# vm asset options
create_asset_action.add_argument('--domain-name', help="VM domain name")
create_asset_action.add_argument('--psu-num', type=int, default=1, help="Number of PSUs installed in the server")
create_asset_action.add_argument(
    '--psu-load', 
    nargs='+',
    type=float,
    help="How much power PSU(s) draw (the downstream power is multiplied by the value, e.g. for 2 PSUs if '--psu-load 0.5 0.5', load is divivided equally) \n"
)

# configure existing asset
configure_asset_action = subparsers.add_parser('configure', help="Configure Asset properties")
configure_asset_action.add_argument('-k', '--asset-key', type=int, required=True)
configure_asset_action.add_argument('--host')
configure_asset_action.add_argument('--on-delay', type=int, help="Power on delay in ms", default=-1)
configure_asset_action.add_argument('--off-delay', type=int, help="Power on delay in ms", default=-1)
configure_asset_action.add_argument('--power-source', type=int)
configure_asset_action.add_argument('--power-consumption', type=int, help="Power consumption in Watts")

# detach & delete an asset by key
delete_asset_action = subparsers.add_parser('delete', help="Remove individual asset by key")
delete_asset_action.add_argument('-k', '--asset-key', type=int, required=True)

# drop entire system topology
drop_system_action = subparsers.add_parser('drop', help="Delete/drop all the system components")

# link 2 assets together
power_asset_action = subparsers.add_parser('power-link', help="Create a power link between 2 assets")
power_asset_action.add_argument(
    '-s', '--source-key', type=int, required=True, help="Key of an asset that POWERS dest. asset"
)
power_asset_action.add_argument('-d', '--dest-key', type=int, required=True, help="Key of an powered by the source-key")

## -> Setup options for power_group

subparsers = power_group.add_subparsers()
power_up_action = subparsers.add_parser('up', help="Power up a particular component/asset")
power_up_action.add_argument('-k', '--asset-key', type=int, required=True)

power_down_action = subparsers.add_parser('down', help="Power down a particular component/asset")
power_down_action.add_argument('-k', '--asset-key', type=int, required=True)

############ Callbacks for actions

status_group.set_defaults(func=lambda args: get_status(**args))

oid_group.set_defaults(func=lambda _: print('Not Implemented Yet'))
snapshot_group.set_defaults(func=lambda _: print('Not Implemented Yet'))

## asset_group callbacks
create_asset_action.set_defaults(
    func=lambda args: create_asset(**args)
)

configure_asset_action.set_defaults(
    func=lambda args: sm.set_properties(args['asset_key'], args)
)

delete_asset_action.set_defaults(
    func=lambda args: sm.delete_asset(args['asset_key'])
)

power_asset_action.set_defaults(
    func=lambda args: sm.link_assets(args['source_key'], args['dest_key'])
)

drop_system_action.set_defaults(func=lambda args: sm.drop_model())

## power_group callbacks
power_up_action.set_defaults(
    func=lambda args: manage_state(args['asset_key'], lambda asset: asset.power_up())
)

power_down_action.set_defaults(
    func=lambda args: manage_state(args['asset_key'], lambda asset: asset.shut_down())
)


try:
    options = argparser.parse_args()
    options.func(vars(options))
except AttributeError:
    argparser.print_help()
except argparse.ArgumentTypeError as e:
    print(e)
