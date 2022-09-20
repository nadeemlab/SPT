import argparse

import spatialprofilingtoolbox
from spatialprofilingtoolbox import get_workflow
from spatialprofilingtoolbox import get_workflow_names
from spatialprofilingtoolbox import get_initializer
workflows = {name : get_workflow(name) for name in get_workflow_names()}
    
if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog = 'spt workflow initialize',
        description = 'A job that runs before all the main (parallelizable) jobs.',
    )

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
