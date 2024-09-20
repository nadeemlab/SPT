
import pandas as pd

from sqlite_stuff import get_sqlite_connection

def check_record_counts():
    connection = get_sqlite_connection()
    table_names = ['measurement_events', 'measurement_values', 'feature_matrix']
    dfs = [pd.read_sql_query(f"SELECT * FROM {table_name}", connection) for table_name in table_names]

    print('Checking record counts for 3 tables found in sqlite database file.')
    print('')
    expected_counts = [4, 24, 3]
    for expected_count, table_name, df in zip(expected_counts, table_names, dfs):
        if expected_count != df.shape[0]:
            raise ValueError(f'Expected {expected_count} in {table_name} but got {df.shape[0]}.')
        else:
            print(f'Got expected record count {expected_count} in {table_name}.')

if __name__=='__main__':
    check_record_counts()
