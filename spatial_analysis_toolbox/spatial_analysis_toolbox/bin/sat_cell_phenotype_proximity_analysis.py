#!/usr/bin/env python3
import os
from os.path import join
import argparse

import spatial_analysis_toolbox
from spatial_analysis_toolbox.api import get_analyzer
from spatial_analysis_toolbox.environment.log_formats import colorized_logger

logger = colorized_logger(__name__)

parser = argparse.ArgumentParser(
    description = ''.join([
        'This program does cell phenotype-phenotype proximity calculations in multiplexed IF images.',
        'It is formulated as a script so that it can be run as part of large HPC batches. '
        'It generally needs to be run as part of sat-pipeline, to ensure proper initialization.',
    ])
)
parser.add_argument('--input-path',  # Look this up from file metadata instead?
    dest='input_path',
    type=str,
    required=True,
    help='Path to input files.',
)
parser.add_argument('--input-file-identifier',
    dest='input_file_identifier',
    type=str,
    required=True,
    help='The input file to process.',
)
parser.add_argument('--outcomes-file',
    dest='outcomes_file',
    type=str,
    help='Path to tabular file containing a column of sample identifiers and a column of outcome assignments.',
)
parser.add_argument('--output-path',
    dest='output_path',
    type=str,
    required=True,
    help='Path to directory where output files should be written.',
)
parser.add_argument('--elementary-phenotypes-file',
    dest='elementary_phenotypes_file',
    type=str,
    required=True,
    help='File containing metadata about the channels/observed phenotypes.',
)
parser.add_argument('--complex-phenotypes-file',
    dest='complex_phenotypes_file',
    type=str,
    required=True,
    help='File specifying signatures for phenotype combinations of interest.',
)
parser.add_argument('--job-index',
    dest='job_index',
    type=str,
    required=True,
    help='Integer index into job activity table.',
)

args = parser.parse_args()

input_path = args.input_path
input_file_identifier = args.input_file_identifier
outcomes_file = args.outcomes_file
output_path = args.output_path
elementary_phenotypes_file = args.elementary_phenotypes_file
complex_phenotypes_file = args.complex_phenotypes_file
job_index = args.job_index

kwargs = {}
kwargs['input_path'] = input_path
kwargs['input_file_identifier'] = input_file_identifier
kwargs['outcomes_file'] = outcomes_file
kwargs['output_path'] = output_path
kwargs['elementary_phenotypes_file'] = elementary_phenotypes_file
kwargs['complex_phenotypes_file'] = complex_phenotypes_file
kwargs['job_index'] = job_index

a = get_analyzer(
    workflow='Multiplexed IF phenotype proximity',
    **kwargs,
)
a.calculate()
