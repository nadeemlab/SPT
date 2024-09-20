# Usage pattern

By convention of this repository, the "curation" steps are:
1. [`./download.sh`](#1-download-source-data)
2. [`./extract.sh`](#2-extract-what-is-needed-and-save-it-to-the-generated-artifacts-subdirectory)
3. [`./verify.sh`](#3-verify-that-the-generated-artifacts-are-as-expected-by-doing-some-checks)
4. [`./clean.sh`](#5-cleandelete-all-intermediate-and-final-generated-artifacts-as-needed) (optional)

Prepared, curated artifacts should be saved to `generated_artifacts/`.

For a real dataset you would of course write your own version of `download.sh`, `extract.sh`, `verify.sh`, `clean.sh`, etc., and commit these to version control.

In this dummy example, the output is as follows:

```txt
$ ./download.sh
SourceData_March_10_2023.zip is present.

$ ./extract.sh
Example during-processing output, e.g. for debugging:

Measurement event ID Subject of measurement  Type code
              ABC_30                0000012          0
              ABC_31                0000047          0
              ABC_32                0000012          3
              ABC_33                0000299          5

Measurement event ID  Value
              ABC_30  1.001
              ABC_30  1.002
              ABC_30  1.003
              ABC_30  1.004
              ABC_30  1.005
              ABC_30  1.006
              ABC_31  1.001
              ABC_31  1.002
              ABC_31  1.003
              ABC_31  1.004
              ABC_31  1.005
              ABC_31  1.006
              ABC_32  2.001
              ABC_32  2.002
              ABC_32  2.003
              ABC_32  2.004
              ABC_32  2.005
              ABC_32  2.006
              ABC_33  3.001
              ABC_33  3.002
              ABC_33  3.003
              ABC_33  3.004
              ABC_33  3.005
              ABC_33  3.006

Identifier Feature 1 Feature 2
   0000012   0.12345   0.78910
   0000047   1.00123   2.17891
   0000299    13.270   0.00002

$ ./verify.sh
Checking record counts for 3 tables found in sqlite database file.

Got expected record count 4 in measurement_events.
Got expected record count 24 in measurement_values.
Got expected record count 3 in feature_matrix.

$ ./clean.sh
Deleted SourceData/ and generated_artifacts/ .
```

## 1. Download source data
```sh
./download.sh
```
`download.sh`:
```sh
#!/bin/bash

# The "download.sh" script should typically fetch a big source data file.
# Something like:
#     wget https://data-repository-hub.com/123456789/SourceData_March_10_2023.zip
#
# In this dummy example case we'll pretend this (committed) zip file was downloaded by this script:
#     SourceData_March_10_2023.zip

main_source_file=SourceData_March_10_2023.zip

if [[ -f $main_source_file ]];
then
    echo "$main_source_file is present."
else
    echo "Error: $main_source_file is not present. Not downloaded?"
    exit 1
fi
```

## 2. Extract what is needed and save it to the generated artifacts subdirectory
```sh
./extract.sh
```
`extract.sh`:
```sh
#!/bin/bash
unzip SourceData_March_10_2023.zip
echo ''
python extract.py
```
`extract.py`:
```py
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
```

This step creates the sqlite database file `generated_artifacts/example_curated_dataset.db` .

## 3. Verify that the generated artifacts are as expected, by doing some checks
```sh
./verify.sh
```
`verify.sh`:
```sh
#!/bin/bash
python verify.py
```
`verify.py`:
```py
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
```

## 4. Clean/delete all intermediate and final generated artifacts, as needed
```sh
./clean.sh
```
`clean.sh`:
```sh
#!/bin/bash
rm -rf SourceData/
rm -rf generated_artifacts/
echo "Deleted SourceData/ and generated_artifacts/ ."
```
