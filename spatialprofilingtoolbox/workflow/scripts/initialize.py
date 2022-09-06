import argparse

def do_library_imports():
    import spatialprofilingtoolbox
    from spatialprofilingtoolbox.module_load_error import SuggestExtrasException
    from spatialprofilingtoolbox import get_workflow
    from spatialprofilingtoolbox import get_workflow_names
    from spatialprofilingtoolbox import get_initializer
    try:
        workflows = {name : get_workflow(name) for name in get_workflow_names()}
    except ModuleNotFoundError as e:
        SuggestExtrasException(e, 'workflow')
    
if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog = 'spt workflow initialize',
        description = 'One parallelizable "core" computation job.',
    )
    do_library_imports()

    for Initializer in [w.initializer for w in workflows.values()]:
        Initializer.solicit_cli_arguments(parser)

    parser.add_argument(
        '--workflow',
        dest='workflow',
        choices=get_workflow_names(),
        required=True,
    )

    parameters = vars(parser.parse_args())
    initializer = get_initializer(**parameters)
    initializer.initialize(**parameters)
