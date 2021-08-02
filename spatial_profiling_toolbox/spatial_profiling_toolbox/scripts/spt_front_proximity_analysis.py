#!/usr/bin/env python3
"""
This script represents a single job of the front proximity analysis workflow. It
is not run directly by the user.
"""
import argparse

import spatialprofilingtoolbox as spt

if __name__=='__main__':
    parser = argparse.ArgumentParser(
        description = ''.join([
            'This program does cell phenotype-to-region-front proximity calculations in ',
            'multiplexed IF images.',
            'It is formulated as a script so that it can be run as part of large HPC batches. '
            'It generally needs to be run as part of spt-pipeline, to ensure initialization.',
        ])
    )
    parser.add_argument('--input-file-identifier',
        dest='input_file_identifier',
        type=str,
        required=True,
        help='The input file to process.',
    )
    parser.add_argument('--job-index',
        dest='job_index',
        type=str,
        required=True,
        help='Integer index into job activity table.',
    )

    args = parser.parse_args()

    kwargs = {}
    kwargs['input_file_identifier'] = args.input_file_identifier
    kwargs['job_index'] = args.job_index

    parameters = spt.get_config_parameters_from_file()
    kwargs['input_path'] = parameters['input_path']
    kwargs['outcomes_file'] = parameters['outcomes_file']
    kwargs['output_path'] = parameters['output_path']
    kwargs['elementary_phenotypes_file'] = parameters['elementary_phenotypes_file']
    kwargs['complex_phenotypes_file'] = parameters['complex_phenotypes_file']

    a = spt.get_analyzer(
        workflow='Multiplexed IF front proximity',
        **kwargs,
    )
    a.calculate()
