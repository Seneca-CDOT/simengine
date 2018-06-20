#!/usr/bin/env python3
""" Command line interface for enginecore """
# pylint: disable=C0103

import argparse
import json
import time
import curses

from enginecore.state.assets import SUPPORTED_ASSETS
from enginecore.state.graph_reference import GraphReference
from enginecore.state.state_managers import StateManger
from enginecore.state.utils import get_asset_type

def manage_state(asset_key, action):
    """ Perform action for a node/asset with a certain key
    Args:
            asset_key (int): supplied asset identifier
            action (func): callable object (lambda/function etc) that identifies action
    """
    with GraphReference().get_session() as session:
        
        asset_info = GraphReference.get_asset_and_components(session, asset_key)
        
        asset_type = get_asset_type(asset_info['labels'])
        state_manager = SUPPORTED_ASSETS[asset_type].StateManagerCls(asset_info)
        
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
    headers = ["Asset Key", "Type", "Status", "Children"]
    row_format = "{:>10}" * (len(headers) + 1)

    headers = row_format.format("", *headers, end='')
    if stdscr: 
        stdscr.addstr(0, 0, headers)
    else:
        print(headers)

    for i, asset_key in enumerate(assets):
        asset = assets[asset_key]
        children = str(asset['children'] if 'children' in asset else "none")
        row = row_format.format(str(i), *[str(asset_key), asset['type'], str(asset['status']), children], end='')

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


################ Define Command line options & arguments

argparser = argparse.ArgumentParser(
    description='Simengine CLI provides a set of management tools for the engine core'
)
subparsers = argparser.add_subparsers()

power_group = subparsers.add_parser('power', help="Control power component of registered asset(s)")

## -> Setup options for state queries
status_group = subparsers.add_parser('status', help="Retrieve status of registered asset(s)")
status_group.add_argument('--asset-key')
status_group.add_argument('--print-as', help="Format options")
status_group.add_argument('--monitor', help="Monitor status", action='store_true')
status_group.add_argument('--load', help="Check load", action='store_true')

status_group.add_argument('--watch-rate', nargs='?', 
                          help="Update state every n seconds, defaults to 1", default=1, type=int)


## -> Setup options for oid queries
oid_group = subparsers.add_parser('oid', help="Manage OIDs")

## -> Setup options for snapshot commands
snapshot_group = subparsers.add_parser('snapshot', help="Manage snapshots of the assets' states")

## -> Setup options for power_group
subparsers = power_group.add_subparsers()
power_up_action = subparsers.add_parser('up', help="Power up a particular component/asset")
power_up_action.add_argument('--asset-key', required=True)

power_down_action = subparsers.add_parser('down', help="Power down a particular component/asset")
power_down_action.add_argument('--asset-key', required=True)

############ Callbacks for actions
power_up_action.set_defaults(
    func=lambda args: manage_state(args['asset_key'], lambda asset: asset.power_up())
)

power_down_action.set_defaults(
    func=lambda args: manage_state(args['asset_key'], lambda asset: asset.power_down())
)

status_group.set_defaults(func=lambda args: get_status(**args))

oid_group.set_defaults(func=lambda _: print('Not Implemented Yet'))
snapshot_group.set_defaults(func=lambda _: print('Not Implemented Yet'))

# try:
options = argparser.parse_args()
options.func(vars(options))
# except:
argparser.print_help()