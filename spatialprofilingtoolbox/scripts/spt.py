import argparse
import sys
import subprocess
import importlib
import re

import spatialprofilingtoolbox
from spatialprofilingtoolbox import submodule_names


def get_commands(submodule_name):
    files = importlib.resources.files('spatialprofilingtoolbox.%s' % submodule_name)
    scripts = [
        re.search('/scripts/(.*)$', str(entry))
        for entry in (files / 'scripts').iterdir()
    ]
    return sorted([
        re.sub(r'\.(py|sh)$', '', script.group(1))
        for script in scripts
        if script and (not re.search(r'^__.*__(\.py)?$', script.group(1)))
    ])


def get_executable_and_script(submodule_name, script_name):
    full_script_name = None
    if importlib.resources.is_resource('spatialprofilingtoolbox.%s.scripts' % submodule_name, '%s.py' % script_name):
        executable = sys.executable
        full_script_name = '%s.py' % script_name
    if importlib.resources.is_resource('spatialprofilingtoolbox.%s.scripts' % submodule_name, '%s.sh' % script_name):
        executable = '/bin/bash'
        full_script_name = '%s.sh' % script_name
    if full_script_name is None:
        raise ValueError('Did not locate %s from submodule "%s".' % (script_name, submodule_name))
    with importlib.resources.path('spatialprofilingtoolbox.%s.scripts' % submodule_name, full_script_name) as path:
        script_path = path
    return executable, script_path


def main_program():
    parser = argparse.ArgumentParser(
        prog='spt',
        description = 'spatialprofilingtoolbox commands',
    )
    parser.add_argument(
        'module',
        choices=[name for name in submodule_names if len(get_commands(name)) > 0],
        help='The specific submodule the command is from.',
    )
    parser.add_argument(
        'command',
        nargs='?',
        default=None,
        help='The command name.',
    )
    parser.add_argument(
        'command_arguments',
        nargs='*',
        help='Arguments passed to the command.',
    )
    if len(sys.argv) >= 4 and sys.argv[3] in ['-h', '--help']:
        sys_args = [arg for arg in sys.argv if not arg in ['-h', '--help']][1:]
        args = parser.parse_args(sys_args)
    else:
        args = parser.parse_args()

    if args.command is None:
        commands = get_commands(args.module)
        print('    '.join(commands))
        exit()

    executable, script_path = get_executable_and_script(args.module, args.command)

    if len(sys.argv) >= 3:
        executable, script_path = get_executable_and_script(args.module, args.command)

    if len(sys.argv) == 3 and sys.argv[1] == args.module and sys.argv[2] == args.command:
        subprocess.run([
            executable,
            script_path,
            '--help',
        ])
        exit()

    if len(sys.argv) > 3 and sys.argv[1] == args.module and sys.argv[2] == args.command:
        executable, script_path = get_executable_and_script(args.module, args.command)
        unparsed_arguments = sys.argv[3:]
        subprocess.run([
            executable,
            script_path,
        ] + unparsed_arguments)
        exit()
