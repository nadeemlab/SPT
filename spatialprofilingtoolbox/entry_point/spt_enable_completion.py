import importlib.resources
from os.path import expanduser
from os.path import join
from os.path import exists
import argparse

from jinja2 import Environment
from jinja2 import BaseLoader

from spatialprofilingtoolbox.entry_point.spt import get_commands
from spatialprofilingtoolbox import submodule_names

header = '### Start added by spatialprofilingtoolbox'
footer = '### End added by spatialprofilingtoolbox'


def remove_previous_installation(filename):
    with open(filename, 'rt') as file:
        contents = file.read()
    header_index = None
    footer_index = None
    try:
        header_index = contents.index(header)
    except ValueError:
        pass
    try:
        footer_index = contents.index(footer)
    except ValueError:
        pass
    if (not header_index is None) and (not footer_index is None):
        startpoint = header_index - 1
        endpoint = footer_index + len(footer) + 1
        new_contents = contents[0:startpoint] + contents[endpoint:]
        with open(filename, 'wt') as file:
            file.write(new_contents)
            print('Removed previous completion code from %s' % filename)


def get_nontrivial_module_names():
    return [name for name in submodule_names if len(get_commands(name)) > 0]


def get_modules_and_commands():
    return [
        {
            'name': module_name,
            'command_names_joined_space': ' '.join(get_commands(module_name)),
            'command_names_joined_bar': '|'.join(["'%s'" % c for c in get_commands(module_name)]),
        }
        for module_name in get_nontrivial_module_names()
    ]


def create_completions_script():
    jinja_environment = Environment(
        loader=BaseLoader, comment_start_string='###')
    with importlib.resources.path('spatialprofilingtoolbox.entry_point',
                                  'spt-completion.sh.jinja') as path:
        with open(path, 'r') as file:
            template_source = file.read().rstrip('\n')
    template = jinja_environment.from_string(template_source)
    modules = get_modules_and_commands()
    return template.render(
        module_names=' '.join(get_nontrivial_module_names()), modules=modules)


def attempt_append_to(filename, contents):
    full_path = join(expanduser('~'), filename)
    if exists(full_path):
        remove_previous_installation(full_path)
        with open(full_path, 'a') as file:
            file.write(contents)
        print('Wrote completions script fragment to:\n %s' % full_path)
        print('Either open a new shell or do:')
        print('    source %s' % full_path)
        exit()


def main_program():
    parser = argparse.ArgumentParser(
        prog='spt-enable-completion',
        description='Enable/disable tab completion for spatialprofilingtoolbox commands.',
    )
    parser.add_argument(
        '--disable',
        dest='disable',
        action='store_true',
        help='Disable completions, i.e. uninstall the bash complete snippet from profile '
        'configuration files.'
    )
    args = parser.parse_args()

    profile_files = ['.bash_profile', '.bashrc', '.profile']
    if args.disable:
        for file in profile_files:
            path = join(expanduser('~'), file)
            if exists(path):
                remove_previous_installation(path)
        exit()

    completion_script = create_completions_script()
    wrapped = '\n%s\n%s\n%s\n' % (header, completion_script, footer)

    for file in profile_files:
        attempt_append_to(join(expanduser('~'), file), wrapped)
