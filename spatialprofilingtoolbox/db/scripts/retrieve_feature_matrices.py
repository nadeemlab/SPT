"""Convenience CLI wrapper of FeatureMatrixExtractor functionality, writes to files."""

import argparse
import json
from os.path import exists
from os.path import abspath
from os.path import expanduser
from typing import cast

from pandas import DataFrame

from spatialprofilingtoolbox.standalone_utilities.module_load_error import \
    SuggestExtrasException
try:
    from spatialprofilingtoolbox.db.feature_matrix_extractor import FeatureMatrixExtractor
    from spatialprofilingtoolbox.db.feature_matrix_extractor import StudyBundle
except ModuleNotFoundError as e:
    SuggestExtrasException(e, 'db')
from spatialprofilingtoolbox.db.feature_matrix_extractor import FeatureMatrixExtractor
from spatialprofilingtoolbox.db.feature_matrix_extractor import StudyBundle

from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument


def retrieve(args: argparse.Namespace):
    database_config_file = None
    if args.database_config_file:
        database_config_file = abspath(expanduser(args.database_config_file))
        if not exists(database_config_file):
            message = f'Need to supply valid database config filename: {database_config_file}'
            raise FileNotFoundError(message)
    extractor = FeatureMatrixExtractor(database_config_file=database_config_file)
    bundle = cast(StudyBundle, extractor.extract(args.study_name))
    feature_matrices = cast(dict[str, dict[str, DataFrame | str]], bundle['feature matrices'])
    for _, specimen_data in feature_matrices.items():
        df = cast(DataFrame, specimen_data['dataframe'])
        filename = cast(str, specimen_data['filename'])
        df.to_csv(filename, sep='\t', index=False)
    outcomes = cast(DataFrame, bundle['sample cohorts']['assignments'])
    filename = 'assignments.tsv'
    outcomes.to_csv(filename, sep='\t', index=False)
    FeatureMatrixExtractor.redact_dataframes(bundle)
    with open('features.json', 'wt', encoding='utf-8') as file:
        file.write(json.dumps(bundle, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt db retrieve-feature-matrices',
        description='''
Retrieve feature matrices for each sample of a study and corresponding outcomes
dataframe and column/channel names lookup from any database that conforms to
"single cell ADI" database schema and writes them as TSV files to the current
working directory, with filenames listed alongside specimen and channel name
information in: features.json
''',

    )
    add_argument(parser, 'database config')
    add_argument(parser, 'study name')
    retrieve(parser.parse_args())
