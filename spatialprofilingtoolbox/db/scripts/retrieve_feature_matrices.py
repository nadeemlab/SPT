"""
Convenience CLI wrapper of FeatureMatrixExtractor functionality, writes to
files.
"""
import argparse
import json
from os.path import exists
from os.path import abspath
from os.path import expanduser

from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt db create-schema')

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
    args = parser.parse_args()

    if args.database_config_file:
        database_config_file = abspath(expanduser(args.database_config_file))
        if not exists(database_config_file):
            raise FileNotFoundError(
                f'Need to supply valid database config filename: {database_config_file}'
            )

    from spatialprofilingtoolbox.standalone_utilities.module_load_error import \
        SuggestExtrasException
    try:
        from spatialprofilingtoolbox.db.feature_matrix_extractor import FeatureMatrixExtractor
    except ModuleNotFoundError as e:
        SuggestExtrasException(e, 'db')

    bundle = FeatureMatrixExtractor.extract(database_config_file)

    for study_name, study in bundle.items():
        for specimen, specimen_data in study['feature matrices']:
            df = specimen_data['dataframe']
            filename = specimen_data['filename']
            df.to_csv(filename, sep='\t', index=False)
        outcomes = study['outcomes']['dataframe']
        filename = study['outcomes']['filename']
        outcomes.to_csv(filename, sep='\t', index=False)
    FeatureMatrixExtractor.redact_dataframes(bundle)
    with open('features.json', 'wt', encoding='utf-8') as file:
        file.write(json.dumps(bundle, indent=2))
