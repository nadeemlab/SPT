from pickle import load

import os
import sys
import json
import re
from os.path import join

import pandas as pd

data_directory = 'test/countsserver/test_expression_data'
with open(join(data_directory, 'centroids.pickle'), 'rb') as file:
    centroids = load(file)

json_files = [
    f for f in os.listdir(data_directory)
    if os.path.isfile(join(data_directory, f)) and re.search(r'\.json$', f)
]

if len(json_files) != 1:
    logger.error('Did not find index JSON file.')
    sys.exit(1)

index_file = join(data_directory, json_files[0])

with open(index_file, 'rt', encoding='utf-8') as file:
    root = json.loads(file.read())
    entries = root[list(root.keys())[0]]
    studies = {}
    for entry in entries:
        studies[entry['specimen measurement study name']] = entry

key = list(studies.keys())[0]
study = studies[key]

filename = join(data_directory, 'expression_data_array.0.0.bin')

columns = list(study['target by symbol'].keys())

rows = []
with open(filename, 'rb') as file:
    buffer = None
    while buffer != b'':
        buffer = file.read(8)
        integer64 = int.from_bytes(buffer, 'little')
        row = list(map(int, list(bin(integer64)[2:].ljust(len(columns), '0'))))
        rows.append(row)

df = pd.DataFrame(rows, columns=columns)


df.head()
df.tail()
rows[0]
rows[99]
rows[100]

tuple(df.loc[0]) == tuple(rows[0])

all(tuple(df.loc[j]) == tuple(rows[j]) for j in range(100))

# 4912,4958,-6,30,1,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0
# ...
# 5312,5348,276,304,1,1,0,1,1,0,0,1,1,0,0,0,1,0,0,0,0,1,0,1,1,0,0,0,0,1

# Conclusion: There is an extraneous 0 row in rows... might be reading some kind of ending byte?