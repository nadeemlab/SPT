#!/usr/bin/env python3
import argparse
import os
from os.path import exists
from os.path import join
from os.path import basename

import spatialprofilingtoolbox
from spatialprofilingtoolbox.standalone_utilities.module_load_error import SuggestExtrasException
from spatialprofilingtoolbox import get_workflow_names
from spatialprofilingtoolbox import get_workflow

if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog = 'spt workflow generate-run-information',
        description='''
        Create a list of core, parallelizable job specifications for a given SPT
        workflow, as well as lists of file dependencies.
        
        Note: Due to orchestration design constraints, if this script must
        depend on file contents, it can *only* depend on the contents of explicitly
        indicated files. That is, it cannot "bootstrap" and open files whose names
        are discovered by reading other files' contents.
        ''',
    )

    parser.add_argument(
        '--workflow',
        dest='workflow',
        type=str,
        choices=get_workflow_names(),
        required=True,
    )
    parser.add_argument(
        '--file-manifest-file',
        dest='file_manifest_file',
        type=str,
        required=True,
        help='''
        Path to the file manifest file. If just a file basename, it is presumed to be
        in the current working directory, since this script is presumed to be
        deployed as a Nextflow process.
        ''',
    )
    parser.add_argument(
        '--input-path',
        dest='input_path',
        type=str,
        required=True,
        help='''Path to directory containing input data files. (For example,
        containing file_manifest.tsv).
        ''',
    )
    parser.add_argument(
        '--outcomes-file',
        dest='outcomes_file',
        type=str,
        required=False,
        help='File containing outcome assignments to Sample ID values.',
    )
    parser.add_argument(
        '--job-specification-table',
        dest='job_specification_table',
        type=str,
        required=True,
        help='Filename for output, job specification table CSV.',
    )
    parser.add_argument(
        '--elementary-phenotypes-filename',
        dest='elementary_phenotypes_filename',
        type=str,
        required=True,
        help='Filename for output, the elementary phenotypes filename.',
    )
    parser.add_argument(
        '--composite-phenotypes-filename',
        dest='composite_phenotypes_filename',
        type=str,
        required=True,
        help='Filename for output, the composite phenotypes filename.',
    )

    args = parser.parse_args()

    if not exists(args.file_manifest_file):
        raise FileNotFoundError(args.file_manifest_file)

    try:
        workflows = {name : get_workflow(name) for name in get_workflow_names()}
    except ModuleNotFoundError as e:
        SuggestExtrasException(e, 'workflow')

    Generator = workflows[args.workflow].generator
    DatasetDesign = workflows[args.workflow].dataset_design
    job_generator = Generator(
        file_manifest_file=args.file_manifest_file,
        input_path=args.input_path,
        dataset_design_class=DatasetDesign,
    )
    job_generator.write_job_specification_table(args.job_specification_table, outcomes_file=args.outcomes_file)
    job_generator.write_elementary_phenotypes_filename(args.elementary_phenotypes_filename)
    job_generator.write_composite_phenotypes_filename(args.composite_phenotypes_filename)
