"""Invoker of the initialize phase of a Nextflow-managed workflow."""
import argparse

from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox import get_workflow
from spatialprofilingtoolbox import get_workflow_names
from spatialprofilingtoolbox import get_initializer

workflows = {name: get_workflow(name) for name in get_workflow_names()}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt workflow initialize',
        description='A job that runs before all the main (parallelizable) jobs.',
    )

    for Initializer in [w.initializer for w in workflows.values()]:
        Initializer.solicit_cli_arguments(parser)

    add_argument(parser, 'workflow')

    parameters = vars(parser.parse_args())

    initializer = get_initializer(**parameters)
    initializer.initialize(**parameters)
