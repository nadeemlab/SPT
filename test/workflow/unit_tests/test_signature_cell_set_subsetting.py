from os.path import join
import sys

import pandas as pd


def get_pandas_signature(df, signature):
    return [
        all(row[key] == 1 if value=='+' else row[key] == 0 for key, value in signature.items())
        for i, row in df.iterrows()
    ]


if __name__ == '__main__':
    filename = join('..', 'test_data', 'adi_preprocessed_tables/dataset1', '0.csv')
    cells = pd.read_csv(filename, sep=',', keep_default_na=False)

    signature1 = get_pandas_signature(cells, {'CD3_Positive': '+', 'B2M_Positive': '+'})
    computed_sum = sum(1 for entry in signature1 if entry)
    if computed_sum != 27:
        print(f'Got computed sum: {computed_sum}')
        sys.exit(1)

    signature2 = get_pandas_signature(cells,
        {'PD1_Positive': '+', 'FOXP3_Positive': '-', 'CD3_Positive': '+'})
    computed_sum = sum(1 for entry in signature2 if entry)
    if computed_sum != 4:
        print(f'Got computed sum: {computed_sum}')
        sys.exit(1)
