"""Test presence of fractions features and assessments of them."""
from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker

if __name__=='__main__':
    with DatabaseConnectionMaker(database_config_file='../db/.spt_db.config.container') as dcm:
        connection = dcm.get_connection()
        cursor = connection.cursor()
        cursor.execute('''
        SELECT
            fs.specifier,
            qfv.subject,
            qfv.value
        FROM feature_specifier fs
        JOIN quantitative_feature_value qfv ON qfv.feature=fs.feature_specification
        ;
        ''')
        rows = [(row[0], row[1], float(row[2])) for row in cursor.fetchall()]
        known_cases = [
            ('cleaved PARP', 'BaselTMA_SP42_5_X8Y7', 0.31289374212515747),
            ('CD20', 'lesion 0_3', 0.050000),
        ]
        print('Got fractions:')
        for row in rows:
            print(row)
        print('')
        print('Testing cases:')
        for case in known_cases:
            print(case)
            assert case in rows
