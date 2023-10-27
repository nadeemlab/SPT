"""Utility to report study names in database."""
import argparse

from spatialprofilingtoolbox.db.database_connection import get_and_validate_database_config
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.standalone_utilities.module_load_error import SuggestExtrasException
try:
    from spatialprofilingtoolbox.db.database_connection import retrieve_study_names
except ModuleNotFoundError as e:
    SuggestExtrasException(e, 'db')
from spatialprofilingtoolbox.db.database_connection import retrieve_study_names

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt db list-studies')

def report_studies(database_config_file):
    study_names = retrieve_study_names(database_config_file)
    for study in study_names:
        print(study)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt db list-studies',
        description='List the studies in the given database.'
    )
    add_argument(parser, 'database config')
    args = parser.parse_args()

    config_file = get_and_validate_database_config(args)
    report_studies(config_file)
