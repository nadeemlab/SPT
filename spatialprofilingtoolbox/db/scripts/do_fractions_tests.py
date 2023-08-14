"""CLI utility to run t-tests for each phenotype fractions feature."""
import argparse
import re

from spatialprofilingtoolbox.db.database_connection import get_and_validate_database_config
from spatialprofilingtoolbox import DatabaseConnectionMaker
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.workflow.common.two_cohort_feature_association_testing import \
    perform_tests

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt db create-schema')

def get_fractions_studies(connection):
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM data_analysis_study;')
    rows = cursor.fetchall()
    cursor.close()
    return [row[0] for row in rows if re.search('phenotype fractions', row[0])]

def do_tests(database_config_file):
    with DatabaseConnectionMaker(database_config_file=database_config_file) as dcm:
        connection = dcm.get_connection()
        fractions_studies = get_fractions_studies(connection)
        for data_analysis_study in fractions_studies:
            perform_tests(data_analysis_study, connection)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt db do-fractions-tests',
        description='Do t-tests for each pair of cohorts, along fractions features.'
    )
    add_argument(parser, 'database config')
    args = parser.parse_args()
    config_file = get_and_validate_database_config(args)
    do_tests(config_file)
