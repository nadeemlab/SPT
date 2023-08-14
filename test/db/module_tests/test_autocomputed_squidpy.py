"""
Test the computation and saving of the Squidpy metrics that depend on a single phenotype, and so
can be computed automatically after data import if desired.
"""

from spatialprofilingtoolbox.db.squidpy_metrics import create_and_transcribe_squidpy_features
from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker

def test_autocomputed_squidpy_features():
    database_config_file='.spt_db.config.container'
    study = 'Melanoma intralesional IL2'
    with DatabaseConnectionMaker(database_config_file=database_config_file) as dcm:
        create_and_transcribe_squidpy_features(dcm, study)


if __name__=='__main__':
    test_autocomputed_squidpy_features()
