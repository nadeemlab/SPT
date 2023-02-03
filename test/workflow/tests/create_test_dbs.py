import sqlite3

import pandas as pd


def generate_test_sqlite_databases():
    db_to_csvs = {
        'data/example_db1.db': ['data/example_db1_table1.csv', 'data/example_db1_table2.csv'],
        'data/example_db2.db': ['data/example_db2_table1.csv', 'data/example_db2_table2.csv'],
    }
    tables = {key: [pd.read_csv(filename).drop('id', axis=1)
                    for filename in filenames] for key, filenames in db_to_csvs.items()}

    for db_file, (df1, df2) in tables.items():
        connection = sqlite3.connect(db_file)
        df1.to_sql('table1', connection, if_exists='append', index_label='id')
        df2.to_sql('table2', connection, if_exists='append', index_label='id')
        connection.commit()
        connection.close()


if __name__ == '__main__':
    generate_test_sqlite_databases()
