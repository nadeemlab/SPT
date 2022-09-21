import argparse
import os
from os.path import exists
from os.path import abspath
from os.path import expanduser
import importlib.resources

import spatialprofilingtoolbox
from spatialprofilingtoolbox.standalone_utilities.module_load_error import SuggestExtrasException
try:
    from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
    import adisinglecell
    import pandas as pd
except ModuleNotFoundError as e:
    SuggestExtrasException(e, 'db')

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
logger = colorized_logger('spt db status')

def check_tables(cursor):
    with importlib.resources.path('adisinglecell', 'tables.tsv') as path:
        tables = pd.read_csv(path, sep='\t', keep_default_na=False)    
    tablenames = list(tables['Name'])
    cursor.execute('SELECT tablename FROM pg_tables WHERE schemaname=\'public\';')
    rows = cursor.fetchall()
    values = [row[0] for row in rows]
    missing = list(set(tablenames).difference(values))
    if len(missing) == 0:
        tables_present = True
    else:
        logger.error('Expected table(s) not found: %s', missing)
        tables_present = False
    counts = []
    for tablename in tablenames:
        cursor.execute('SELECT COUNT(*) FROM public.%s' % tablename)
        rows = cursor.fetchall()
        count = rows[0][0]
        counts.append([tablename, count])
    return tables_present, counts

def report_counts(counts):
    df = pd.DataFrame({
        'Table' : [row[0] for row in counts],
        'Records' : [row[1] for row in counts],
    })
    print(df.sort_values(by='Table').to_string(index=False))

if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog = 'spt db status',
        description = 'Report basic health status of the given scstudies database.'
    )
    parser.add_argument(
        '--database-config-file',
        dest='database_config_file',
        type=str,
        required=False,
        help='Provide the file for database configuration.',
    )
    args = parser.parse_args()

    if args.database_config_file:
        config_file = abspath(expanduser(args.database_config_file))
    if not exists(config_file):
        raise FileNotFoundError('Need to supply valid database config filename: %s', config_file)

    dcm = DatabaseConnectionMaker(database_config_file=config_file)
    connection = dcm.get_connection()
    cursor = connection.cursor()
    tables_present, counts = check_tables(cursor)
    if not tables_present:
        exit(1)
    cursor.close()
    connection.close()
    report_counts(counts)

