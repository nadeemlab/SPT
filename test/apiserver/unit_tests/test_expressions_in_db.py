import os

from spatialprofilingtoolbox.apiserver.app.db_accessor import DBAccessor


def test_one_expression_vector():
    environment = {
        'SINGLE_CELL_DATABASE_HOST': 'spt-db-testing',
        'SINGLE_CELL_DATABASE_USER': 'postgres',
        'SINGLE_CELL_DATABASE_PASSWORD': 'postgres',
        'USE_ALTERNATIVE_TESTING_DATABASE': '1',
    }

    for key, value in environment.items():
        os.environ[key] = value

    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
        cursor.execute('''
        SELECT
        hsi.histological_structure,
        cs.symbol
        FROM expression_quantification eq
        JOIN histological_structure_identification hsi ON hsi.histological_structure=eq.histological_structure
        JOIN data_file df ON df.sha256_hash=hsi.data_source
        JOIN specimen_data_measurement_process sdmp ON sdmp.identifier=df.source_generation_process
        JOIN chemical_species cs ON cs.identifier=eq.target
        WHERE sdmp.specimen=%s AND eq.discrete_value=%s
        ORDER BY hsi.histological_structure, cs.symbol
        ;
        ''', ('lesion 0_1', 'positive'))
        rows = cursor.fetchall()
        cursor.close()

    for key in environment.keys():
        os.environ.pop(key)

    expected = set([('0', 'B2M'), ('0', 'B7H3'), ('0', 'DAPI'), ('0', 'MHCI')])
    print(expected)
    print(set(rows[0:4]))
    assert(set(rows[0:4]) == expected)

    expected = set([('1', 'B2M'), ('1', 'B7H3'), ('1', 'DAPI'), ('1', 'KI67'), ('1', 'MHCI'), ('1', 'MRC1'), ('1', 'S100B'), ('1', 'SOX10')])
    print(expected)
    print(set(rows[4:12]))
    assert(set(rows[4:12]) == expected)


if __name__=='__main__':
    test_one_expression_vector()