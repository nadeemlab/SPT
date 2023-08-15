"""
Test the computation and saving of the Squidpy metrics that depend on a single phenotype, and so
can be computed automatically after data import if desired.
"""

from pandas import read_csv

from spatialprofilingtoolbox.db.squidpy_metrics import create_and_transcribe_squidpy_features
from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.db.squidpy_metrics import describe_spatial_autocorr_derivation_method


def get_expected_records():
    filename = 'module_tests/expected_auto_correlations.tsv'
    df = read_csv(filename, sep='\t', header=None)
    df.columns = ['feature', 'sample', 'value']
    df['feature'] = df['feature'].astype(str)
    df['sample'] = df['sample'].astype(str)
    df['value'] = df['value'].astype(float)
    df['value'] = df['value'].apply(round6)
    return [tuple(row) for _, row in df.iterrows()]


def check_records(feature_values):
    rows = [(row[0], row[1], round6(row[2])) for row in feature_values]
    missing = set(get_expected_records()).difference(rows)
    if len(missing) > 0:
        raise ValueError(f'Expected to find records: {missing}')
    print('All expected records found.')
    unexpected = set(rows).difference(get_expected_records())
    if len(unexpected) > 0:
        raise ValueError(f'Got some unexpected records: {unexpected}')
    print('No unexpected records encountered.')


def round6(value):
    return int(pow(10, 6) * value) / pow(10, 6)


def retrieve_feature_values(connection):
    cursor = connection.cursor()
    cursor.execute(f'''
    SELECT fs.identifier, qfv.subject, qfv.value FROM quantitative_feature_value qfv
    JOIN feature_specification fs ON fs.identifier=qfv.feature
    WHERE fs.derivation_method='{describe_spatial_autocorr_derivation_method()}'
    ;
    ''')
    rows = cursor.fetchall()
    cursor.close()
    return [(row[0], row[1], float(row[2])) for row in rows]


def test_autocomputed_squidpy_features():
    database_config_file='.spt_db.config.container'
    study = 'Melanoma intralesional IL2'
    with DatabaseConnectionMaker(database_config_file=database_config_file) as dcm:
        create_and_transcribe_squidpy_features(dcm, study)
        feature_values = retrieve_feature_values(dcm.get_connection())
    print('\n'.join([str(r) for r in feature_values[0:10]] + ['...']))
    check_records(feature_values)


if __name__=='__main__':
    test_autocomputed_squidpy_features()
