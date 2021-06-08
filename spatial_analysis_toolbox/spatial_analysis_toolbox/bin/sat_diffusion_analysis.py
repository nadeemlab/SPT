#!/usr/bin/env python
import os
import argparse
import re

import numpy as np
import pandas as pd

import spatial_analysis_toolbox
from spatial_analysis_toolbox.dataset_designs.multiplexed_immunofluorescence.design import HALOCellMetadataDesign  # Go through factory_api
from spatial_analysis_toolbox.api import get_analyzer
from spatial_analysis_toolbox.environment.log_formats import colorized_logger

def unquote_spaces(f):
    return re.sub(r'\\ ', ' ', f)

if __name__=='__main__':
    logger = colorized_logger(__name__)

    parser = argparse.ArgumentParser(
        description = ''.join([
            'This program does calculations with multiplexed IF images. ',
            'It is formulated as a script so that it can be run as part of large HPC batches. '
            'It generally needs to be run as part of sat-pipeline, to ensure proper initialization.',
        ])
    )
    parser.add_argument('--input-path',
        dest='input_path',
        type=str,
        required=True,
        help='Path to input files.',
    )
    parser.add_argument('--input-file-identifier',
        dest='input_file_identifier',
        type=str,
        required=True,
        help='Input file identifier, as it appears in the file manifest.',
    )
    parser.add_argument('--fov',
        dest='input_fov',
        type=int,
        required=True,
        help='Ordinality of field of view to consider (i.e. one-based integer index).',
    )
    parser.add_argument('--regional-compartment',
        dest='regional_compartment',
        type=str,
        required=True,
        help='?',
    )
    parser.add_argument('--output-path',
        dest='output_path',
        type=str,
        required=True,
        help='Path to directory where output files should be written.',
    )
    parser.add_argument('--outcomes-file',
        dest='outcomes_file',
        type=str,
        required=True,
        help='Path to tabular file containing a column of sample identifiers and a column of outcome assignments.',
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

    kwargs = {}
    kwargs['fov_index'] = args.input_fov
    kwargs['regional_compartment'] = args.regional_compartment
    kwargs['output_path'] = args.output_path        # Some of these arguments can be obtained directly from the configuration file
    kwargs['outcomes_file'] = args.outcomes_file
    kwargs['input_file_identifier'] = args.input_file_identifier
    kwargs['input_path'] = args.input_path
    kwargs['elementary_phenotypes_file'] = args.elementary_phenotypes_file
    kwargs['complex_phenotypes_file'] = args.complex_phenotypes_file
    kwargs['job_index'] = args.job_index

    design = HALOCellMetadataDesign(args.elementary_phenotypes_file, args.complex_phenotypes_file)

    a = get_analyzer(
        workflow='Multiplexed IF diffusion',
        **kwargs,
    )
    a.calculate()
