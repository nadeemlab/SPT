import re
from os.path import join
import sys
import toml

def load_dockerfile(submodule):
    with open(join('build', submodule, 'Dockerfile'), 'rt', encoding='utf-8') as file:
        contents = file.read()
    return contents

def check_exists(dependency, dockerfile):
    for line in dockerfile.split('\n'):
        if re.search(f'RUN python3? -m pip install "?{dependency}"?$', line):
            return True
        if re.search(dependency, line):
            print(f'Dependency "{dependency}" is mentioned in Dockerfile, but something isn\'t quite right with installation command.')
            return False
    return False

def main():
    submodules = sys.argv[1:]
    dockerfiles = {submodule: load_dockerfile(submodule) for submodule in submodules}
    project = toml.load('pyproject.toml.unversioned')
    for submodule, dockerfile in dockerfiles.items():
        dependencies = project['project']['optional-dependencies'][submodule]
        for dependency in dependencies:
            if not check_exists(dependency, dockerfile):
                print(f'Something wrong with dependencies ({dependency}) in Dockerfile "{submodule}".')
                sys.exit(1)
    print('All Dockerfiles have expected Python package dependencies mentioned correctly.')

if __name__=='__main__':
    main()
