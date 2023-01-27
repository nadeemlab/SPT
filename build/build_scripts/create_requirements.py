"""
A simple utility to create a flat list of package requirements strings starting
from the pyproject.toml format. This is used to do pre-installation of
requirements for a package using pip.

If a command-line argument is supplied, it is expected to be the name of an
installation extra, and then the requirements printed are just those for the
extra.
"""
import sys
import toml


def main():
    project = toml.load('pyproject.toml')
    requirements = project['project']['dependencies']
    if len(sys.argv) > 1:
        extra = sys.argv[1]
        optionals = project['project']['optional-dependencies']
        if extra not in optionals:
            raise ValueError(f'{extra} not in pyproject.toml extras.')
        requirements = optionals[extra]
    print('\n'.join(requirements))


if __name__ == '__main__':
    main()
