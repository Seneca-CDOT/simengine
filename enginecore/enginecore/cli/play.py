"""CLI endpoints for managing and executing playback related commands
"""
import os 
from enginecore.state.api import IStateManager


def display_plays(plays):
    """Show a list of available scenarios"""

    show_scripts_of_type = lambda t, p: print('{}:\n {}'.format(t, '\n '.join(p)))

    show_scripts_of_type('Bash Scripts', plays[0])
    show_scripts_of_type('Python Scripts', plays[0])


def play_command(power_group):
    """CLI endpoints for managing assets' power states & wallpower"""
    play_subp = power_group.add_subparsers()
    
    folder_action = play_subp.add_parser('folder', help="Update user-defined script folder")
    folder_action.add_argument(
        '-p', '--path', type=str, required=True, help="Path to the folder containing playback scripts"
    )

    folder_action.set_defaults(
        func=lambda args: IStateManager.set_play_path(os.path.abspath(args['path']))
    )

    list_action = play_subp.add_parser('list', help="List scripts available for execution")


    list_action.set_defaults(
        func=lambda args: display_plays(IStateManager.plays())
    )
