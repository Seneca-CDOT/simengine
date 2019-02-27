"""CLI endpoints for managing and executing playback related commands
"""
import os 
import enginecore.model.system_modeler as sys_modeler

def play_command(power_group):
    """CLI endpoints for managing assets' power states & wallpower"""
    play_subp = power_group.add_subparsers()
    
    folder_action = play_subp.add_parser('folder', help="Update user-defined script folder")
    folder_action.add_argument(
        '-p', '--path', type=str, required=True, help="Path to the folder containing playback scripts"
    )

    folder_action.set_defaults(
        func=lambda args: sys_modeler.set_play_path(os.path.abspath(args['path']))
    )
