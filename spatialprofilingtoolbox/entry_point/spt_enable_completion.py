import importlib.resources
import os
from os.path import expanduser
from os.path import join
from os.path import exists
import re

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

def attempt_append_to(filename, contents):
    remove_previous_installation(filename)
    full_path = join(expanduser('~'), filename)
    if exists(full_path):
        with open(full_path, 'a') as file:
            file.write(contents)
        print('Wrote completions script fragment to:\n %s' % full_path)
        exit()

def main_program():
    with importlib.resources.path('spatialprofilingtoolbox.entry_point', 'spt-completion.sh') as path:
        with open(path, 'r') as file:
            completion_script = file.read().rstrip('\n')
    lines = completion_script.split('\n')
    completion_script = '\n'.join(lines[1:])
    wrapped = '\n%s\n%s\n%s\n' % (header, completion_script, footer)

    attempt_append_to(join(expanduser('~'), '.bash_profile'), wrapped)
    attempt_append_to(join(expanduser('~'), '.profile'), wrapped)
    attempt_append_to(join(expanduser('~'), '.bashrc'), wrapped)