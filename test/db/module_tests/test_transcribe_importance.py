"""Test that transcription of importance scores from GNN output into the database succeeds."""
from pandas import DataFrame

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.db.importance_score_transcriber import transcribe_importance
from spatialprofilingtoolbox import get_feature_description


def get_test_importance_rows():
    return [
        (119, 0.80),
        (120, 0.81),
        (121, 0.82),
        (122, 0.83),
        (123, 0.84),
        (124, 0.85),
        (125, 0.86),
        (126, 0.10),
    ]


def get_expected_records():
    return [
        (119, 1),
        (120, 2),
        (121, 3),
        (122, 4),
        (123, 5),
        (124, 6),
        (125, 7),
        (126, 0),
    ]


def check_records(feature_values):
    rows = [(row[0], row[1]) for row in feature_values]
    missing = set(get_expected_records()).difference(rows)
    if len(missing) > 0:
        raise ValueError(f'Expected to find records: {missing}')
    print('All expected records found.')
    unexpected = set(rows).difference(get_expected_records())
    if len(unexpected) > 0:
        raise ValueError(f'Got some unexpected records: {unexpected}')
    print('No unexpected records encountered.')


def retrieve_feature_values(connection):
    cursor = connection.cursor()
    cursor.execute(f'''
    SELECT * FROM quantitative_feature_value qfv
    JOIN feature_specification fs ON fs.identifier=qfv.feature
    WHERE fs.derivation_method='{get_feature_description("gnn importance score")}'
    ;
    ''')
    rows = cursor.fetchall()
    cursor.close()
    return [(int(row[2]), int(row[3])) for row in rows]


def test_transcribe_importances():
    columns = ['histological_structure', 'importance_score']
    df = DataFrame(get_test_importance_rows(), columns=columns)
    df = df.set_index('histological_structure')
    with DatabaseConnectionMaker(database_config_file='../db/.spt_db.config.container') as dcm:
        connection = dcm.get_connection()
        transcribe_importance(df, connection)
        feature_values = retrieve_feature_values(connection)
    check_records(feature_values)


if __name__ == '__main__':
    test_transcribe_importances()
