"""
Generate test data artifacts representing expected return values for test queries for population
fractions among the selected GNN-most-important cells.
"""

from json import dumps

from pandas import read_csv
from pandas import Series

def get_file_by_sample():
    filename = 'test/test_data/adi_preprocessed_tables/dataset1/file_manifest.tsv'
    manifest = read_csv(filename, sep='\t')
    rows = [row for _, row in manifest.iterrows() if row['Data type'] == 'Tabular cell manifest']
    return {
        row['Sample ID']: row['File name']
        for row in rows
    }

def get_importances():
    importances_filename = 'test/test_data/adi_preprocessed_tables/dataset1/importances.csv'
    importances = read_csv(importances_filename, sep=',')
    importances['histological_structure'] = importances['histological_structure'].astype(str)
    importances.set_index('histological_structure', inplace=True)
    return importances

def get_expression_dfs():
    importances = get_importances()
    expression_dfs = {
        f'{i}.csv': read_csv(
            f'test/test_data/adi_preprocessed_tables/dataset1/{i}.csv',
            sep=',',
            keep_default_na=False,
        )
        for i in range(7)
    }
    offset = 0
    for filename in [
        f'{i}.csv'
        for i in range(7)
    ]:
        df = expression_dfs[filename]
        df['histological_structure'] = [str(offset + i) for i in range(100)]
        df.set_index('histological_structure', inplace=True)
        offset = offset + df.shape[0]

        joined = df.join(importances, on='histological_structure')
        joined = joined.sort_values(by='importance_score', ascending=False)
        rank = Series([i+1 for i in range(joined.shape[0])], joined.index)
        df['rank'] = rank
    return expression_dfs

def get_counts(signature, expression_dfs):
    counts = {}
    for filename, df in expression_dfs.items():
        cell_limit = 50
        df2 = df.loc[df['rank'] <= cell_limit]
        assert df2.shape[0] == cell_limit
        conditions = [df2[channel_name] == value for channel_name, value in signature]
        condition = conditions[0] & conditions[1] & conditions[2]
        selection = df2[condition]
        counts[filename] = selection.shape[0]
    counts_by_sample = {
        sample: counts[get_file_by_sample()[sample]]
        for sample in get_file_by_sample()
    }
    return counts_by_sample

def generate():
    expression_dfs = get_expression_dfs()

    signature = [('CD3_Positive', 1), ('CD4_Positive', 1), ('CD8_Positive', 1)]
    counts_by_sample = get_counts(signature, expression_dfs)
    print(dumps(counts_by_sample, indent=4))
    print(sum(count for _, count in counts_by_sample.items()))

    print('')

    signature = [('CD3_Positive', 0), ('CD4_Positive', 0), ('CD8_Positive', 0)]
    counts_by_sample = get_counts(signature, expression_dfs)
    print(dumps(counts_by_sample, indent=4))
    print(sum(count for _, count in counts_by_sample.items()))

if __name__=='__main__':
    generate()
