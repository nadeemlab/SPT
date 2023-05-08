
import sys
import toml

def main():
    project = toml.load('pyproject.toml.unversioned')
    version = open('version.txt', 'rt', encoding='utf-8').read().rstrip()
    project['project']['version'] = version
    new_contents = toml.dumps(project)
    with open('pyproject.toml', 'wt', encoding='utf-8') as file:
        file.write(new_contents)

if __name__=='__main__':
    main()
