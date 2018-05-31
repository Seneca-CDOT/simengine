#!/usr/bin/env python3
""" Command line interface """
# pylint: disable=C0103

import argparse
from enginecore.state.assets import SUPPORTED_ASSETS
from enginecore.state.graph_reference import GraphReference

def manage_state(asset_key, action):
    """ Perform action for a node/asset with a certain key
    Args:
            asset_key (int): supplied asset identifier
            action (func): callable object (lambda/function etc) that identifies action
    """
    with GraphReference().get_session() as session:
        labels = GraphReference.get_node_by_key(session, asset_key)
        asset_label = set(SUPPORTED_ASSETS).intersection(
            map(lambda x: x.lower(), labels)
        )

        state_manager = SUPPORTED_ASSETS[next(iter(asset_label), '').lower()].get_state_manager(asset_key)
        action(state_manager)


################ Define Command line options & arguments

argparser = argparse.ArgumentParser(
    description='Simengine CLI provides a set of management tools for the engine core'
)
subparsers = argparser.add_subparsers() #help='sub-command help', dest='subparser_name')

power_group = subparsers.add_parser('power', help="Control power component of registered asset(s)")
status_group = subparsers.add_parser('status', help="Retrieve status of registered asset(s)")
oid_group = subparsers.add_parser('oid', help="Manage OIDs")

## Setup options for power_group
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

status_group.set_defaults(func=lambda _: print('Not Implemented Yet'))
oid_group.set_defaults(func=lambda _: print('Not Implemented Yet'))

options = argparser.parse_args()
options.func(vars(options))
