#!/usr/bin/env python3
import os
from os.path import exists
import sqlite3
import re
import argparse

def get_table_names(uri):
    connection = sqlite3.connect(uri)
    result = connection.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = sorted([name[0] for name in result.fetchall()])
    table_names = [t for t in table_names if not re.search('^sqlite', t)]
    return table_names

def get_column_names(table_name, db):
    connection = sqlite3.connect(db)
    cursor = connection.execute('select * from %s limit 1' % table_name)
    return sorted([row[0] for row in cursor.description])

def serialize_list_for_sql(items):
    return '"' + '","'.join(items) + '"'

def migrate_table(table_name, input_db, output_db):
    columns = get_column_names(table_name, input_db)
    if 'id' in columns:
        columns.remove('id')

    connection = sqlite3.connect(input_db)
    query = 'SELECT %s FROM %s' % (serialize_list_for_sql(columns), table_name)
    df = pd.read_sql(query, connection, index_col=None)
    connection.close()

    connection = sqlite3.connect(output_db)
    df.to_sql(table_name, connection, if_exists='append', index=False)
    connection.close()

def compute_performance_filename(db_filename):
    return db_filename.rstrip('.db') + '.csv'


if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog = 'spt workflow merge-sqlite-dbs',
        description = ''.join([
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

    import spatialprofilingtoolbox
    from spatialprofilingtoolbox.standalone_utilities.module_load_error import SuggestExtrasException
    try:
        import pandas as pd
    except ModuleNotFoundError as e:
        SuggestExtrasException(e, 'workflow')

    input_dbs = args.input_dbs
    output_db = args.output
    if exists(output_db):
        print('%s already exists. Aborting.' % output_db)
        exit()

    connection = sqlite3.connect(output_db)
    connection.close()

    table_names = get_table_names(input_dbs[0])
    for input_db in input_dbs:
        these_table_names = get_table_names(input_db)
        if table_names != these_table_names:
            print('Table names %s and %s do not match in input databases. Aborting.' % (table_names, these_table_names))
            exit()
        for name in table_names:
            migrate_table(name, input_db, output_db)
