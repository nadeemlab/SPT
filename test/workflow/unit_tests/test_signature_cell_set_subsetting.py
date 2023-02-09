from os.path import join
import sys

import pandas as pd

from spatialprofilingtoolbox.workflow.tabular_import.tabular_dataset_design \
    import TabularCellMetadataDesign

if __name__ == '__main__':
    dataset_design = TabularCellMetadataDesign(
        elementary_phenotypes_file=join(
            '..', 'test_data', 'adi_preprocessed_tables/dataset1', 'elementary_phenotypes.csv'),
    )
    cells = pd.read_csv(join('..', 'test_data', 'adi_preprocessed_tables/dataset1',
                        '0.csv'), sep=',', keep_default_na=False)

    signature = dataset_design.get_pandas_signature(
        cells, {'CD3': '+', 'B2M': '+'})
    computed_sum = sum(1 for entry in signature if entry)
    if computed_sum != 27:
        print(f'Got computed sum: {computed_sum}')
        sys.exit(1)

    signature = dataset_design.get_pandas_signature(
        cells, {'PD1': '+', 'FOXP3': '-', 'CD3': '+'})
    computed_sum = sum(1 for entry in signature if entry)
    if computed_sum != 4:
        print(f'Got computed sum: {computed_sum}')
        sys.exit(1)
