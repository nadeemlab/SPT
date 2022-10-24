import os

import spatialprofilingtoolbox
from spatialprofilingtoolbox.apiserver.app.db_accessor import DBAccessor


if __name__=='__main__':
    environment = {
        'SINGLE_CELL_DATABASE_HOST' : 'spt-db-testing',
        'SINGLE_CELL_DATABASE_USER' : 'postgres',
        'SINGLE_CELL_DATABASE_PASSWORD' : 'postgres',
        'USE_ALTERNATIVE_TESTING_DATABASE' : '1',
    }

    for key, value in environment.items():
        os.environ[key] = value

    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT COUNT(*) FROM specimen_measurement_study;')
        rows = cursor.fetchall()
        count = rows[0][0]
        cursor.close()

    for key in environment.keys():
        os.environ.pop(key)

    if count != 1:
        print('Number of specimen_measurement_study rows was: %s' % count)
        exit(1)
