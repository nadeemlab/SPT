"""
Utility to drop or recreate certain constraints in the single-cell ADI SQL
schema. Used to boost performance of certain operations.
"""
import argparse
from os.path import exists
from os.path import abspath
from os.path import expanduser
from enum import Enum
from enum import auto
import importlib.resources
import re

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
logger = colorized_logger('modify-constraints')


class DBConstraintsToggling(Enum):
    """Request type for modification of the DB constraints."""
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
    return re.sub(r'[ \-]', '_', name).lower()


def get_constraint_status(cursor):
    query = f'''
    SELECT DISTINCT
        pg_constraint.contype as connection_type,
        pg_constraint.conname as constraint_name,
        pg_class.relname as relation_name
    FROM pg_trigger
    JOIN pg_class ON pg_trigger.tgrelid = pg_class.oid
    JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace 
    JOIN pg_constraint ON pg_constraint.oid = pg_trigger.tgconstraint
    WHERE relname IN {str(tuple(big_tables()))}
    ORDER BY relname, constraint_name;
    '''
    cursor.execute(query)

    column_names = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    return [column_names, rows]


def get_constraint_design():
    with importlib.resources.path('adiscstudies', 'fields.tsv') as path:
        fields = pd.read_csv(path, sep='\t', na_filter=False)
    foreign_key_constraints = [
        [normalize(str(s)) for s in [row['Table'], row['Name'],
                                     row['Foreign table'], row['Foreign key'], row['Ordinality']]]
        for i, row in fields.iterrows()
        if row['Foreign table'] != '' and row['Foreign key'] != ''
        and (normalize(row['Table']) in big_tables())
    ]
    return foreign_key_constraints


def print_constraint_status(column_names, info_rows):
    def print_formatted(row):
        return print(f"{row[0]:<16} {row[1]:<65} {row[2]:<40}")
    logger.info('Printing constraint info.')
    print_formatted(column_names)
    for row in info_rows:
        print_formatted(row)


def toggle_constraints(
    database_config_file,
    state: DBConstraintsToggling = DBConstraintsToggling.RECREATE,
):
    with DatabaseConnectionMaker(database_config_file) as dcm:
        cursor = dcm.get_connection().cursor()
        try:
            if state == DBConstraintsToggling.RECREATE:
                pattern = '''
                ALTER TABLE %s 
                ADD CONSTRAINT %s 
                FOREIGN KEY (%s) 
                REFERENCES %s (%s);'''
                for tablename, field_name, foreign_tablename, foreign_field_name, ordinality \
                        in get_constraint_design():
                    statement = pattern % (
                        tablename,
                        f'{tablename}{ordinality}',
                        field_name,
                        foreign_tablename,
                        foreign_field_name,
                    )
                    logger.debug('Executing: %s', statement)
                    cursor.execute(statement)
                column_names, info_rows = get_constraint_status(cursor)
                print_constraint_status(column_names, info_rows)

            if state == DBConstraintsToggling.DROP:
                pattern = '''
                ALTER TABLE %s
                DROP CONSTRAINT IF EXISTS %s;'''
                column_names, info_rows = get_constraint_status(cursor)
                print_constraint_status(column_names, info_rows)
                for _, constraint_name, tablename in info_rows:
                    statement = pattern % (tablename, constraint_name)
                    logger.debug('Executing: %s', statement)
                    cursor.execute(statement)
        except Exception as exception:
            cursor.close()
            raise exception

        cursor.close()
        dcm.get_connection().commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt db modify-constraints',
        description='''Drop/recreate constraints on certain tables (the largest ones).
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
        help='The file for database configuration. The user specified must have elevated privilege.'
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

    from spatialprofilingtoolbox.standalone_utilities.module_load_error import \
        SuggestExtrasException
    try:
        import pandas as pd
        from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker # pylint: disable=ungrouped-imports
    except ModuleNotFoundError as e:
        SuggestExtrasException(e, 'db')

    database_config_file_elevated = abspath(
        expanduser(args.database_config_file_elevated))
    if not exists(database_config_file_elevated):
        raise FileNotFoundError(
            f'Need to supply valid database config filename, not: {database_config_file_elevated}')

    if args.recreate:
        db_state = DBConstraintsToggling.RECREATE
    elif args.drop:
        db_state = DBConstraintsToggling.DROP
    else:
        raise ValueError('--recreate or --drop must be flagged.')

    toggle_constraints(database_config_file_elevated, state=db_state)
