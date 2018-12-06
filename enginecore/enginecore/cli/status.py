"""This module aggregates command-line interface for assets' status subparser"""

import json
import time
import curses
from enginecore.state.assets import Asset
from enginecore.state.state_managers import StateManager


def status_command(status_group):
    """Status of the system"""
    status_group.add_argument('-k', '--asset-key', help="Get status of one asset (by key) ", type=int)
    status_group.add_argument('--json', help="Format as .json", action='store_true')
    status_group.add_argument('--monitor', help="Monitor status", action='store_true')
    status_group.add_argument(
        '--load', help="Get load for the specified asset (key must be provided)", action='store_true'
    )
    status_group.add_argument(
        '--agent', 
        help="Get information about simulator agent (SNMP/IPMI, key must be provided)",
        action='store_true'
    )
    status_group.add_argument('--value-only', help="Return value only", action='store_true')
    status_group.add_argument(
        '--watch-rate', nargs='?', help="Update state every n seconds, defaults to 1", default=1, type=int
    )

    # callbacks
    status_group.set_defaults(func=lambda args: get_status(**args))

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
        children = str("{}...{}".format(asset['children'][0], asset['children'][-1]) if 'children' in asset else "none")
        row = row_format.format(
            str(i), 
            *[str(asset_key), asset['type'], str(asset['status']), children, "{0:.2f}".format(asset['load'])], 
            end=''
        )

        if stdscr:
            stdscr.addstr(
                i+1, 0, row, curses.color_pair(bcolors.ERROR if int(asset['status']) == 0 else bcolors.OKGREEN)
            )
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
    
        state_manager = Asset.get_state_manager_by_key(kwargs['asset_key'])

        if kwargs['value_only']:
            print(state_manager.load)
        else:
            print("{}-{} : {}".format(state_manager.key, state_manager.asset_type, state_manager.load))
        return
    elif kwargs['asset_key'] and kwargs['agent']:
        state_manager = Asset.get_state_manager_by_key(kwargs['asset_key'])
        agent_info = state_manager.agent
        if agent_info:
            msg = "running" if agent_info[1] else "not running"
            if kwargs['value_only']:
                print(int(agent_info[1]))
            else:
                print("{}-{} : pid[{}] is {}".format(state_manager.key, state_manager.asset_type, agent_info[0], msg))
        else:
            print("{}-{} is not running any agents!".format(state_manager.key, state_manager.asset_type))

        return
    elif kwargs['asset_key']:
        state_manager = Asset.get_state_manager_by_key(kwargs['asset_key'])
        if kwargs['value_only']:
            print(state_manager.status)
        else:
            print("{}-{} : {}".format(state_manager.key, state_manager.asset_type, state_manager.status))
        return

    ##### list states #####
    assets = StateManager.get_system_status()

    # json format
    if kwargs['json']: 
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
                assets = StateManager.get_system_status()
        except KeyboardInterrupt:
            pass
        finally:
            curses.echo()
            curses.nocbreak()
            curses.endwin()
            
    # human-readable table
    else:
        status_table_format(assets)
