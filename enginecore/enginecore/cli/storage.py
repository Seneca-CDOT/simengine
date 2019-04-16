"""Storage commands including physical drive status updates, error counter setters for both
controller and cachevault
"""
import argparse
from enginecore.state.net.state_client import StateClient


def process_cmd_result(executed):
    """Process executed command, display error if execution was unsuccessful"""
    if not executed:
        print("Could not process the request!")


def storage_command(storage_group):
    """Manage server storage space"""

    storage_subp = storage_group.add_subparsers()

    pd_command(
        storage_subp.add_parser("pd", help="Physical drive details and configurations")
    )

    controller_command(
        storage_subp.add_parser(
            "controller", help="Update RAID controller related properties"
        )
    )

    cv_command(storage_subp.add_parser("cv", help="Configure cachevault properties"))


def get_ctrl_storage_args():
    """Group together storage related args 
    (most storage commands require at least server asset key and controller number) 
    """

    # group a few args into a common parent element
    server_controller_parent = argparse.ArgumentParser(add_help=False)
    server_controller_parent.add_argument(
        "-k",
        "--asset-key",
        help="Key of the server storage belongs to ",
        type=int,
        required=True,
    )
    server_controller_parent.add_argument(
        "-c",
        "--controller",
        help="Number of the RAID controller",
        type=int,
        required=True,
    )

    return server_controller_parent


def pd_command(pd_group):
    """Endpoints for setting storage props (pd, vd, controller etc.) """

    pd_subp = pd_group.add_subparsers()

    # group a few args into a common parent element
    server_controller_parent = get_ctrl_storage_args()

    # CLI PD setter
    set_pd_action = pd_subp.add_parser(
        "set",
        help="Configure a physical drive (error count, state etc.)",
        parents=[server_controller_parent],
    )

    set_pd_action.add_argument(
        "-d", "--drive-id", help="Physical Drive id (DID)", type=int, required=True
    )

    set_pd_action.add_argument(
        "-m",
        "--media-error-count",
        help="Update media error count for the drive",
        type=int,
    )

    set_pd_action.add_argument(
        "-o",
        "--other-error-count",
        help="Update other error count for the drive",
        type=int,
    )

    set_pd_action.add_argument(
        "-p",
        "--predictive-error-count",
        help="Update error prediction value for the drive",
        type=int,
    )

    set_pd_action.add_argument(
        "-r",
        "--rebuild-time",
        help="Time (in seconds) required to complete rebuild process for a drive",
        type=int,
    )

    set_pd_action.add_argument(
        "-s",
        "--state",
        help="Update state if the physical drive",
        choices=["Onln", "Offln"],
    )

    set_pd_action.set_defaults(
        func=lambda args: process_cmd_result(
            StateClient(args["asset_key"]).set_physical_drive_prop(
                args["controller"], args["drive_id"], args
            )
        )
    )


def controller_command(ctrl_group):
    """Endpoints for setting storage props (pd, vd, controller etc.) """

    ctrl_subp = ctrl_group.add_subparsers()
    server_controller_parent = get_ctrl_storage_args()

    # CLI controller setter
    set_ctrl_action = ctrl_subp.add_parser(
        "set",
        help="Configure a specific RAID controller",
        parents=[server_controller_parent],
    )

    set_ctrl_action.add_argument(
        "-e",
        "--memory-correctable-errors",
        help="Correctable RAM errors on disk data",
        type=int,
        required=False,
        dest="mem_c_errors",
    )

    set_ctrl_action.add_argument(
        "-u",
        "--memory-uncorrectable-errors",
        help="Uncorrectable RAM errors on disk data",
        type=int,
        required=False,
        dest="mem_uc_errors",
    )

    set_ctrl_action.add_argument(
        "-a",
        "--alarm-state",
        help="Controller alarm state",
        choices=["missing", "off", "on"],
        required=False,
        dest="alarm",
    )

    set_ctrl_action.set_defaults(
        func=lambda args: process_cmd_result(
            StateClient(args["asset_key"]).set_controller_prop(args["controller"], args)
        )
    )


def cv_command(cv_group):
    """Endpoints for CacheVault properties"""
    cv_group = cv_group.add_subparsers()

    # CLI PD setter
    set_cv_action = cv_group.add_parser(
        "set", help="Configure CacheVault", parents=[get_ctrl_storage_args()]
    )

    set_cv_action.add_argument(
        "-r",
        "--replacement-required",
        help="Correctable RAM errors on disk data",
        choices=["Yes", "No"],
        required=True,
    )

    set_cv_action.add_argument(
        "-w",
        "--write-through-fail",
        help="Virtual drive endpoint will fail to report its cache mode as WT (WriteThrough)",
        action="store_false",
    )

    set_cv_action.set_defaults(
        func=lambda args: process_cmd_result(
            StateClient(args["asset_key"]).set_cv_replacement(args["controller"], args)
        )
    )
