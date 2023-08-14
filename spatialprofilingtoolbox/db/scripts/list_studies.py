"""Utility to report study names in database."""
import argparse

from spatialprofilingtoolbox.db.database_connection import get_and_validate_database_config
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.standalone_utilities.module_load_error import SuggestExtrasException
try:
    from spatialprofilingtoolbox import DatabaseConnectionMaker
except ModuleNotFoundError as e:
    SuggestExtrasException(e, 'db')
from spatialprofilingtoolbox import DatabaseConnectionMaker

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt db list-studies')

def report_studies(cursor):
    cursor.execute('SELECT study_specifier FROM study;')
    rows = cursor.fetchall()
    for row in rows:
        print(row[0])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt db list-studies',
        description='List the studies in the given database.'
    )
    add_argument(parser, 'database config')
    args = parser.parse_args()

    config_file = get_and_validate_database_config(args)
    with DatabaseConnectionMaker(database_config_file=config_file) as dcm:
        _cursor = dcm.get_connection().cursor()
        report_studies(_cursor)
        _cursor.close()
