"""Test that the database accessor wrapper basically works."""
import os
import sys

from spatialprofilingtoolbox.apiserver.app.db_accessor import DBAccessor


if __name__ == '__main__':
    environment = {
        'SINGLE_CELL_DATABASE_HOST': 'spt-db-testing',
        'SINGLE_CELL_DATABASE_USER': 'postgres',
        'SINGLE_CELL_DATABASE_PASSWORD': 'postgres',
        'USE_ALTERNATIVE_TESTING_DATABASE': '1',
    }

    for key, value in environment.items():
        os.environ[key] = value

    with DBAccessor() as (_, _, cursor):
        cursor.execute('SELECT COUNT(*) FROM specimen_measurement_study;')
        rows = cursor.fetchall()
        count = rows[0][0]

    for key in environment:
        os.environ.pop(key)

    if count != 1:
        print(f'Number of specimen_measurement_study rows was: {count}')
        sys.exit(1)
