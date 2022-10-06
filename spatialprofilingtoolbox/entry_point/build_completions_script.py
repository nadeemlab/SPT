import jinja2
from jinja2 import Environment
from jinja2 import BaseLoader

import spatialprofilingtoolbox
from spatialprofilingtoolbox import submodule_names
from spt import get_commands

nontrivial_module_names = [name for name in submodule_names if len(get_commands(name)) > 0]

def get_modules_and_commands():
    return [
        {
            'name' : module_name,
            'command_names_joined_space' : ' '.join(get_commands(module_name)),
            'command_names_joined_bar' : '|'.join(["'%s'" % c for c in get_commands(module_name)]),
        }
        for module_name in nontrivial_module_names
    ]

if __name__=='__main__':
    jinja_environment = Environment(loader=BaseLoader, comment_start_string='###')
    template = jinja_environment.from_string(open('spt-completion.sh.jinja', 'rt').read())
    modules = get_modules_and_commands()
    completions_script = template.render(module_names=' '.join(nontrivial_module_names), modules=modules)
    with open('spt-completion.sh', 'wt') as file:
        file.write(completions_script)
