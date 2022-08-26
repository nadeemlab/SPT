import importlib
import os
from os.path import expanduser
from os.path import join
from os.path import exists

def attempt_append_to(filename, contents):
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
    wrapped = '\n### Start added by spatialprofilingtoolbox\n%s\n### End added by spatialprofilingtoolbox\n' % completion_script

    attempt_append_to(join(expanduser('~'), '.bash_profile'), wrapped)
    attempt_append_to(join(expanduser('~'), '.profile'), wrapped)
    attempt_append_to(join(expanduser('~'), '.bashrc'), wrapped)
