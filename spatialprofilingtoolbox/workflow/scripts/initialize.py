#!/usr/bin/env python3
import argparse

import spatialprofilingtoolbox
from spatialprofilingtoolbox import workflows
from spatialprofilingtoolbox import get_workflow_names
from spatialprofilingtoolbox import get_initializer

if __name__=='__main__':
    parser = argparse.ArgumentParser(
        description = 'One parallelizable "core" computation job.',
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
