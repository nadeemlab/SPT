import argparse

import spatialprofilingtoolbox
from spatialprofilingtoolbox import get_workflow_names
from spatialprofilingtoolbox import get_workflow
from spatialprofilingtoolbox import get_core_job
workflows = {name : get_workflow(name) for name in get_workflow_names()}


if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog = 'spt workflow core-job',
        description = 'One parallelizable "core" computation job.',
    )

    for CoreJob in [w.core_job for w in workflows.values()]:
        CoreJob.solicit_cli_arguments(parser)

    parser.add_argument(
        '--workflow',
        dest='workflow',
        choices=get_workflow_names(),
        required=True,
    )
    parser.add_argument(
        '--input-file-identifier',
        dest='input_file_identifier',
        type=str,
        required=True,
        help='An input file identifier, as it appears in the file manifest.',
    )
    parser.add_argument(
        '--input-filename',
        dest='input_filename',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--elementary-phenotypes-file',
        dest='elementary_phenotypes_file',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--composite-phenotypes-file',
        dest='composite_phenotypes_file',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--sample-identifier',
        dest='sample_identifier',
        type=str,
        required=True,
        help='The sample identifier associated with the given input file, as it appears in the file manifest.'
    )
    parser.add_argument(
        '--outcome',
        dest='outcome',
        type=str,
        required=True,
        help='The outcome assignment for the sample associated with the given input file.'
    )
    parser.add_argument(
        '--compartments-file',
        dest='compartments_file',
        type=str,
        required=True,
        help='File containing compartment names.'
    )
    parser.add_argument(
        '--metrics-database-filename',
        dest='metrics_database_filename',
        type=str,
        required=True,
        help=''.join([
            'Filename for sqlite database file storing intermediate results.',
        ])
    )

    parameters = vars(parser.parse_args())
    core_job = get_core_job(**parameters)
    core_job.calculate()
