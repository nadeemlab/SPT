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
    from spatialprofilingtoolbox.db.feature_matrix_extractor import Bundle
except ModuleNotFoundError as e:
    SuggestExtrasException(e, 'db')
from spatialprofilingtoolbox.db.feature_matrix_extractor import FeatureMatrixExtractor
from spatialprofilingtoolbox.db.feature_matrix_extractor import Bundle

from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt db create-schema')

def retrieve(args: argparse.Namespace):
    database_config_file = None
    if args.database_config_file:
        database_config_file = abspath(expanduser(args.database_config_file))
        if not exists(database_config_file):
            message = f'Need to supply valid database config filename: {database_config_file}'
            raise FileNotFoundError(message)
    extractor = FeatureMatrixExtractor(database_config_file=database_config_file)
    bundle = cast(Bundle, extractor.extract())
    for _, study in bundle.items():
        feature_matrices = cast(dict[str, dict[str, DataFrame | str ]], study['feature matrices'])
        for _, specimen_data in feature_matrices.items():
            df = cast(DataFrame, specimen_data['dataframe'])
            filename = cast(str, specimen_data['filename'])
            df.to_csv(filename, sep='\t', index=False)
        outcomes = cast(DataFrame, study['sample cohorts']['assignments'])
        filename = 'assignments.tsv'
        outcomes.to_csv(filename, sep='\t', index=False)
    FeatureMatrixExtractor.redact_dataframes(bundle)
    with open('features.json', 'wt', encoding='utf-8') as file:
        file.write(json.dumps(bundle, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt db retrieve-feature-matrices',
        description='''
Retrieve feature matrices for each sample of each study, an outcomes dataframe
for each study, and a column/channel names lookup for each study.
Retrieves from any database that conforms to "single cell ADI" database schema.
Writes TSV files to the current working directory, with filenames listed alongside
specimen and channel name information in:  features.json
'''
    )
    add_argument(parser, 'database config')
    retrieve(parser.parse_args())
