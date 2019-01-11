"""
simengine-cli storage set pd --asset-key=5 --controller=0 --drive-id=12 --media-error-count=2
simengine-cli storage set pd --asset-key=5 --controller=0 --drive-id=12 --other-error-count=2
simengine-cli storage set pd --asset-key=5 --controller=0 --drive-id=12 --predictive-error-count=2

"""
import argparse
from enginecore.state.state_managers import BMCServerStateManager

def storage_command(storage_group):
    """Manage server storage space"""

    storage_subp = storage_group.add_subparsers()

    pd_command(storage_subp.add_parser(
        'pd', 
        help="Physical drive details and configurations"
    ))

    vd_command(storage_subp.add_parser(
        'vd', 
        help="Virtual drive configurations"
    ))

    controller_command(storage_subp.add_parser(
        'controller', 
        help="Update RAID controller related properties"
    ))


def get_ctrl_storage_args():
    # group a few args into a common parent element
    server_controller_parent = argparse.ArgumentParser(add_help=False)
    server_controller_parent.add_argument(
        '-k', '--asset-key', help="Key of the server storage belongs to ", type=int, required=True
    )
    server_controller_parent.add_argument(
        '-c', '--controller', help="Number of the RAID controller", type=int, required=True
    )

    return server_controller_parent


def pd_command(pd_group):
    """Endpoints for setting storage props (pd, vd, controller etc.) """

    pd_subp = pd_group.add_subparsers()

    # group a few args into a common parent element
    server_controller_parent = get_ctrl_storage_args()
    
    # CLI PD setter
    set_pd_action = pd_subp.add_parser(
        'set', 
        help="Configure a physical drive (error count, state etc.)",
        parents=[server_controller_parent]
    )

    set_pd_action.add_argument(
        '-d', '--drive-id', help="Physical Drive id (DID)", type=int, required=True
    )

    set_pd_action.add_argument(
        '-m', '--media-error-count', help="Update media error count for the drive", type=int, required=False
    )

    set_pd_action.add_argument(
        '-o', '--other-error-count', help="Update other error count for the drive", type=int, required=False
    )

    set_pd_action.add_argument(
        '-p', '--predictive-error-count', help="Update error prediction value for the drive", type=int, required=False
    )

    set_pd_action.add_argument(
        '-s', '--state', help="Update state if the physical drive", choices=["Onln", "Offln"], required=False
    )

    set_pd_action.set_defaults(
        func=lambda args: BMCServerStateManager.set_physical_drive_prop(
            args['asset_key'], args['controller'], args['drive_id'], args
        )
    )


def vd_command(vd_group):
    """Confgiguring virtual drive"""
    vd_subp = vd_group.add_subparsers()

    # group a few args into a common parent element
    server_controller_parent = get_ctrl_storage_args()
    
    # CLI virtual drive setter
    set_vd_action = vd_subp.add_parser(
        'set', 
        help="Configure a virtual drive (degraded state props)",
        parents=[server_controller_parent]
    )

    set_vd_action.add_argument(
        '-p', 
        '--partially-degraded', 
        help="Set state to partially degraded at this number of physical drive errors (accumulative)", 
        type=int, 
        required=False
    )

    set_vd_action.add_argument(
        '-d', 
        '--degraded', 
        help="Set state to degraded at this number of physical drive errors (accumulative)", 
        type=int, 
        required=False
    )




def controller_command(ctrl_group):
    """Endpoints for setting storage props (pd, vd, controller etc.) """

    ctrl_subp = ctrl_group.add_subparsers()
    server_controller_parent = get_ctrl_storage_args()

    # CLI controller setter
    set_ctrl_action = ctrl_subp.add_parser(
        'set', 
        help="Configure a specific RAID controller",
        parents=[server_controller_parent]
    )

    set_ctrl_action.add_argument(
        '-e', '--memory-correctable-errors', help="Correctable RAM errors on disk data", type=int, required=False
    )

    set_ctrl_action.add_argument(
        '-u', '--memory-uncorrectable-errors', help="Uncorrectable RAM errors on disk data", type=int, required=False
    )

    set_ctrl_action.add_argument(
        '-a', '--alarm-state', help="Controller alarm state", choices=["missing", "off", "on"], required=False
    )

    set_ctrl_action.set_defaults(
        func=lambda args: BMCServerStateManager.set_controller_prop(
            args['asset_key'], args['controller'], args
        )
    )
