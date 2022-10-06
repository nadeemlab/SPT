import argparse
import os
from os.path import exists
from os.path import abspath
from os.path import expanduser
import enum
from enum import Enum
from enum import auto
import importlib.resources
import re

import spatialprofilingtoolbox
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
logger = colorized_logger('modify-constraints')


class DBConstraintsToggling(Enum):
    RECREATE = auto()
    DROP = auto()


def big_tables():
    return [
        'histological_structure',
        'histological_structure_identification',
        'expression_quantification',
        'shape_file',
    ]


def normalize(name):
    return re.sub('[ \-]', '_', name).lower()


def get_constraint_status(cursor):
    query = '''
    SELECT DISTINCT
        pg_constraint.contype as connection_type,
        pg_constraint.conname as constraint_name,
        pg_class.relname as relation_name
    FROM pg_trigger
    JOIN pg_class ON pg_trigger.tgrelid = pg_class.oid
    JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace 
    JOIN pg_constraint ON pg_constraint.oid = pg_trigger.tgconstraint
    WHERE relname IN %s
    ORDER BY relname, constraint_name;
    ''' % str(tuple(big_tables()))
    cursor.execute(query)

    column_names = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    info_rows = [[entry for entry in row] for row in rows]
    return [column_names, info_rows]


def get_constraint_design():
    with importlib.resources.path('adisinglecell', 'fields.tsv') as path:
        fields = pd.read_csv(path, sep='\t', na_filter=False)
    foreign_key_constraints = [
        [normalize(str(s)) for s in [row['Table'], row['Name'], row['Foreign table'], row['Foreign key'], row['Ordinality']]]
        for i, row in fields.iterrows()
        if row['Foreign table'] != '' and row['Foreign key'] != '' and (normalize(row['Table']) in big_tables())
    ]
    return foreign_key_constraints


def print_constraint_status(column_names, info_rows):
    print_formatted = lambda row: print ("{:<16} {:<65} {:<40}".format(*row))
    logger.info('Printing constraint info.')
    print_formatted(column_names)
    for row in info_rows:
        print_formatted(row)


def toggle_constraints(
    database_config_file_elevated,
    state: DBConstraintsToggling=DBConstraintsToggling.RECREATE,
):
    dcm = DatabaseConnectionMaker(database_config_file_elevated)
    connection = dcm.get_connection()
    cursor = connection.cursor()

    try:
        if state == DBConstraintsToggling.RECREATE:
            pattern = '''
            ALTER TABLE %s 
            ADD CONSTRAINT %s 
            FOREIGN KEY (%s) 
            REFERENCES %s (%s);'''
            foreign_key_constraints = get_constraint_design()
            for tablename, field_name, foreign_tablename, foreign_field_name, ordinality in foreign_key_constraints:
                statement = pattern % (
                    tablename,
                    '%s%s' %(tablename, ordinality),
                    field_name,
                    foreign_tablename,
                    foreign_field_name,
                )
                logger.debug('Executing: %s' % statement)
                cursor.execute(statement)
            column_names, info_rows = get_constraint_status(cursor)
            print_constraint_status(column_names, info_rows)

        if state == DBConstraintsToggling.DROP:
            pattern = '''
            ALTER TABLE %s
            DROP CONSTRAINT IF EXISTS %s;'''
            column_names, info_rows = get_constraint_status(cursor)
            print_constraint_status(column_names, info_rows)
            for connection_type, constraint_name, tablename in info_rows:
                statement = pattern % (tablename, constraint_name)
                logger.debug('Executing: %s' % statement)
                cursor.execute(statement)

    except Exception as e:
        cursor.close()
        connection.close()
        raise e

    cursor.close()
    connection.commit()
    connection.close()


if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog = 'spt db modify-constraints',
        description = '''Drop/recreate constraints on certain tables (the largest ones).
        Can be used to wrap bulk import operations.
        The status of constraints is written to stdout just before dropping or just after
        creation. The meaning of the "connection_type" entry is documented here under "contype":

            https://www.postgresql.org/docs/current/catalog-pg-constraint.html
        '''
    )
    parser.add_argument(
        '--database-config-file-elevated',
        dest='database_config_file_elevated',
        type=str,
        required=True,
        help='The file for database configuration. The user specified must have elevated privileges.',
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--drop',
        action='store_true',
        default=False,
    )
    group.add_argument(
        '--recreate',
        action='store_true',
        default=False,
    )
    args = parser.parse_args()

    from spatialprofilingtoolbox.standalone_utilities.module_load_error import SuggestExtrasException
    try:
        import pandas as pd
        from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
    except ModuleNotFoundError as e:
        SuggestExtrasException(e, 'db')

    database_config_file_elevated = abspath(expanduser(args.database_config_file_elevated))
    if not exists(database_config_file_elevated):
        raise FileNotFoundError('Need to supply valid database config filename, not: %s', database_config_file_elevated)

    if args.recreate:
        state = DBConstraintsToggling.RECREATE
    if args.drop:
        state = DBConstraintsToggling.DROP

    toggle_constraints(database_config_file_elevated, state=state)
