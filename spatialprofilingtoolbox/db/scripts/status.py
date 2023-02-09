"""Utility to report basic health/status of the SPT database."""
import sys
import argparse
import importlib.resources

from spatialprofilingtoolbox.db.database_connection import get_and_validate_database_config
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.standalone_utilities.module_load_error import SuggestExtrasException
try:
    import pandas as pd
    from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker  # pylint: disable=ungrouped-imports
except ModuleNotFoundError as e:
    SuggestExtrasException(e, 'db')

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt db status')


def check_tables(cursor):
    with importlib.resources.path('adiscstudies', 'tables.tsv') as path:
        tables = pd.read_csv(path, sep='\t', keep_default_na=False)
    table_names = list(tables['Name'])
    cursor.execute(
        'SELECT tablename FROM pg_tables WHERE schemaname=\'public\';')
    rows = cursor.fetchall()
    values = [row[0] for row in rows]
    missing = list(set(table_names).difference(values))
    if len(missing) == 0:
        tables_present = True
    else:
        logger.error('Expected table(s) not found: %s', missing)
        tables_present = False
    counts = []
    for tablename in table_names:
        cursor.execute(f'SELECT COUNT(*) FROM public.{tablename}')
        rows = cursor.fetchall()
        count = rows[0][0]
        counts.append([tablename, count])
    return tables_present, counts


def report_counts(counts):
    df = pd.DataFrame({
        'Table': [row[0] for row in counts],
        'Records': [row[1] for row in counts],
    })
    print(df.sort_values(by='Table').to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt db status',
        description='Report basic health status of the given scstudies database.'
    )
    add_argument(parser, 'database config')
    args = parser.parse_args()

    config_file = get_and_validate_database_config(args)
    with DatabaseConnectionMaker(database_config_file=config_file) as dcm:
        cur = dcm.get_connection().cursor()
        present, counted = check_tables(cur)
        if not present:
            sys.exit(1)
        cur.close()

    report_counts(counted)
