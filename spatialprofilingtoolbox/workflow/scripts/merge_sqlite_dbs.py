"""A convenience utility to merge sqlite databases with the same schema."""
from os.path import exists
import sqlite3
import re
import argparse
import sys


def get_table_names(uri):
    connection = sqlite3.connect(uri)
    result = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table';")
    names = sorted([name[0] for name in result.fetchall()])
    names = [t for t in names if not re.search('^sqlite', t)]
    return names


def get_column_names(table_name, database):
    connection = sqlite3.connect(database)
    cursor = connection.execute(f'select * from {table_name} limit 1')
    return sorted([row[0] for row in cursor.description])


def serialize_list_for_sql(items):
    return '"' + '","'.join(items) + '"'


def migrate_table(table_name, in_db, out_db):
    columns = get_column_names(table_name, in_db)
    if 'id' in columns:
        columns.remove('id')

    connection = sqlite3.connect(in_db)
    query = f'SELECT {serialize_list_for_sql(columns)} FROM {table_name}'
    df = pd.read_sql(query, connection, index_col=None)
    connection.close()

    connection = sqlite3.connect(out_db)
    df.to_sql(table_name, connection, if_exists='append', index=False)
    connection.close()


def compute_performance_filename(db_filename):
    return db_filename.rstrip('.db') + '.csv'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt workflow merge-sqlite-dbs',
        description=''.join([
            'Merges multiple input sqlite databases with identical table schemas.',
            'If an "id" column is present, it is removed. No "id" column will ',
            'appear in the output.',
        ])
    )
    parser.add_argument(
        'input_dbs',
        nargs='*',
    )
    parser.add_argument(
        '--output',
        dest='output',
        type=str,
        required=True,
        help='Name of output file to be generated.',
    )
    args = parser.parse_args()

    from spatialprofilingtoolbox.standalone_utilities.module_load_error import \
        SuggestExtrasException
    try:
        import pandas as pd
    except ModuleNotFoundError as e:
        SuggestExtrasException(e, 'workflow')

    input_dbs = args.input_dbs
    output_db = args.output
    if exists(output_db):
        print(f'{output_db} already exists. Aborting.')
        sys.exit()

    conn = sqlite3.connect(output_db)
    conn.close()

    table_names = get_table_names(input_dbs[0])
    for input_db in input_dbs:
        these_table_names = get_table_names(input_db)
        if table_names != these_table_names:
            print(
                f'Table names {table_names} and {these_table_names} do not match in '
                'input databases. Aborting.')
            sys.exit()
        for name in table_names:
            migrate_table(name, input_db, output_db)
