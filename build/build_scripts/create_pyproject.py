"""Create pyproject.toml from unversioned variant."""
import toml


def validate_dependencies_all(project):
    modules = ['apiserver', 'graphs', 'db', 'ondemand', 'workflow']
    dependencies = set()
    for module in modules:
        dependencies = dependencies.union(set(project['project']['optional-dependencies'][module]))
    all_dependencies = sorted(list(dependencies))
    all_prelisted = sorted(list(project['project']['optional-dependencies']['all']))
    print()
    print(list(set(all_dependencies).difference(all_prelisted)))
    print(list(set(all_prelisted).difference(all_dependencies)))
    assert all_dependencies == all_prelisted


def main():
    project = toml.load('pyproject.toml.unversioned')
    with open('version.txt', 'rt', encoding='utf-8') as file:
        version = file.read().rstrip()
    project['project']['version'] = version
    validate_dependencies_all(project)
    new_contents = toml.dumps(project)
    with open('pyproject.toml', 'wt', encoding='utf-8') as file:
        file.write(new_contents)


if __name__ == '__main__':
    main()
