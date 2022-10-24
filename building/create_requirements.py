
import sys
import toml

if __name__=='__main__':
    c = toml.load('pyproject.toml')
    requirements = c['project']['dependencies']
    if len(sys.argv) > 1:
        requirements = c['project']['optional-dependencies'][sys.argv[1]]
    print('\n'.join(requirements))
