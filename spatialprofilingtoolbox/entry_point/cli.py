import argparse
import sys
import subprocess
import importlib.resources
import re
import signal

import spatialprofilingtoolbox
from spatialprofilingtoolbox import submodule_names


def get_commands(submodule_name):
    files = importlib.resources.files(
        f'spatialprofilingtoolbox.{submodule_name}')
    if submodule_name in ['entry_point', 'standalone_utilities']:
        return []
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
    if importlib.resources.is_resource(f'spatialprofilingtoolbox.{submodule_name}.scripts',
                                       f'{script_name}.py'):
        executable = sys.executable
        full_script_name = f'{script_name}.py'
    if importlib.resources.is_resource(f'spatialprofilingtoolbox.{submodule_name}.scripts',
                                       f'{script_name}.sh'):
        executable = '/bin/bash'
        full_script_name = f'{script_name}.sh'
    if full_script_name is None:
        raise ValueError(
            f'Did not locate {script_name} from submodule "{submodule_name}".')
    with importlib.resources.path(f'spatialprofilingtoolbox.{submodule_name}.scripts',
                                  full_script_name) as path:
        script_path = path
    return executable, script_path


def print_version_and_all_commands():
    submodules_with_commands = [
        name for name in submodule_names if len(get_commands(name)) > 0]
    commands_description = '\n\n'.join([
        '\n'.join(
            [f'spt {submodule} {command}' for command in get_commands(submodule)])
        for submodule in submodules_with_commands
    ])
    print(f'Version {spatialprofilingtoolbox.__version__}')
    print('https://github.com/nadeemlab/SPT/')
    print('')
    print(commands_description)


def main_program():
    submodules_with_commands = [
        name for name in submodule_names if len(get_commands(name)) > 0]
    parser = argparse.ArgumentParser(
        prog='spt',
        description='spatialprofilingtoolbox commands',
    )
    parser.add_argument(
        'module',
        choices=submodules_with_commands,
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

    module = None
    if len(sys.argv) >= 2:
        if sys.argv[1] in submodules_with_commands:
            module = sys.argv[1]

    if module is None:
        print_version_and_all_commands()
        exit()

    command = None
    if len(sys.argv) >= 3:
        if sys.argv[2] in get_commands(module):
            command = sys.argv[2]

    if command is None:
        commands = get_commands(module)
        print('    '.join(commands))
        exit()

    if len(sys.argv) == 3:
        exit()

    if len(sys.argv) > 3:
        executable, script_path = get_executable_and_script(module, command)
        unparsed_arguments = sys.argv[3:]
        running_process = subprocess.Popen([
            executable,
            script_path,
        ] + unparsed_arguments)
        signal.signal(signal.SIGTERM, lambda signum,
                      frame: running_process.send_signal(signal.SIGTERM))
        signal.signal(signal.SIGINT, lambda signum,
                      frame: running_process.send_signal(signal.SIGINT))
        exit(running_process.wait())
