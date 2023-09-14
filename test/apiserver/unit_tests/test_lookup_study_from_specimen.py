"""Check functionality of simple lookup of study."""

import os

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.accessors import StudyAccess

def test_lookup():
    environment = {
        'SINGLE_CELL_DATABASE_HOST': 'spt-db-testing',
        'SINGLE_CELL_DATABASE_USER': 'postgres',
        'SINGLE_CELL_DATABASE_PASSWORD': 'postgres',
        'USE_ALTERNATIVE_TESTING_DATABASE': '1',
    }

    for key, value in environment.items():
        os.environ[key] = value

    with DBCursor() as cursor:
        study = StudyAccess(cursor).get_study_from_specimen('lesion 0_1')
        assert study == 'Melanoma intralesional IL2'

if __name__=='__main__':
    test_lookup()
