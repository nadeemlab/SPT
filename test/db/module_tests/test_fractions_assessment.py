"""Test presence of fractions features and assessments of them."""

from pandas import read_csv

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox import get_feature_description

def retrieve_known_cases():
    df = read_csv('module_tests/expected_fractions.tsv', sep='\t')
    df['Fraction'] = df['Fraction'].apply(round6)
    return [tuple(row) for _, row in df.iterrows()]

def round6(value):
    return int(pow(10, 6) * value) / pow(10, 6)

if __name__=='__main__':
    rows = []
    studies = ['Melanoma intralesional IL2', 'Breast cancer IMC']
    for study in studies:
        with DBCursor(database_config_file='../db/.spt_db.config.container', study=study) as cursor:
            cursor.execute('''
            SELECT
                fs.specifier,
                qfv.subject,
                qfv.value
            FROM feature_specifier fs
            JOIN quantitative_feature_value qfv ON qfv.feature=fs.feature_specification
            JOIN feature_specification fsp ON fsp.identifier=fs.feature_specification
            WHERE fsp.derivation_method=%s
            ;
            ''', (get_feature_description('population fractions'),))
            rows.extend([(row[0], row[1], round6(float(row[2]))) for row in cursor.fetchall()])

    known_cases = retrieve_known_cases()
    print(f'Got fractions ({len(rows)}):')
    for i, row in enumerate(sorted(rows)):
        print(row)
        if i > 25:
            print('...')
            break
    print('')
    print(f'Testing {len(known_cases)} cases.')
    for i, case in enumerate(sorted(known_cases)):
        if i < 25:
            print(case)
        if i == 26:
            print('...')
        if not case in rows:
            print(f'Error: {case} is missing.')
        assert case in rows
    print('All present.')
