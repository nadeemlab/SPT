"""Convenience function providing summary of number of records per table."""
from importlib.resources import as_file
from importlib.resources import files

import pandas as pd

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


def check_tables(cursor):
    with as_file(files('adiscstudies').joinpath('tables.tsv')) as path:
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
        count = int(rows[0][0])
        counts.append([tablename, count])
    return tables_present, counts
