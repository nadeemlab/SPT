from os.path import join
from os.path import exists
import json
import sqlite3

import pandas as pd

from sqlite_stuff import initialize_sqlite_db
from sqlite_stuff import get_sqlite_connection

def extract_dataset_from_source_files():
    source_dir = 'SourceData'
    measurement_files = pd.read_csv(join(source_dir, 'spreadsheet2.tsv'), keep_default_na=False, sep='\t', dtype=str)
    measurement_events = []
    measurements = []
    for i, row in measurement_files.iterrows():
        measurement_id = row['ID']
        measurement_file = join(source_dir, row['Associated file'])
        if not exists(measurement_file):
            raise FileNotFoundError(measurement_file)
        with open(measurement_file, 'rt', encoding='utf-8') as file:
            measurement_info = json.loads(file.read())
        measurement_events.append((measurement_id, measurement_info['subject'], measurement_info['measurement code']))
        for value in measurement_info['measurements']:
            measurements.append((measurement_id, value))

    measurement_events_df = pd.DataFrame(measurement_events, columns=['Measurement event ID', 'Subject of measurement', 'Type code'])
    measurements_df = pd.DataFrame(measurements, columns=['Measurement event ID', 'Value'])
    feature_matrix = pd.read_csv(join(source_dir, 'spreadsheet1.tsv'), keep_default_na=False, sep='\t', dtype=str)
    dfs = [measurement_events_df, measurements_df, feature_matrix]

    print_data_frames(dfs)
    initialize_sqlite_db()
    send_to_sqlite(dfs, ['measurement_events', 'measurement_values', 'feature_matrix'])

def send_to_sqlite(dfs, table_names):
    connection = get_sqlite_connection()
    for table_name, df in zip(table_names, dfs):
        df.to_sql(table_name, connection, if_exists='replace', index=False)
    connection.commit()

def print_data_frames(dfs):
    print('Example during-processing output, e.g. for debugging:')
    print('')
    for df in dfs:
        print(df.to_string(index=False))
        print('')

if __name__=='__main__':
    extract_dataset_from_source_files()
