from os.path import join

import pandas as pd

from spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.halo_cell_metadata_design \
    import HALOCellMetadataDesign

if __name__ == '__main__':
    dataset_design = HALOCellMetadataDesign(
        elementary_phenotypes_file=join(
            '..', 'test_data', 'adi_preprocessed_tables/dataset1', 'elementary_phenotypes.csv'),
    )
    cells = pd.read_csv(join('..', 'test_data', 'adi_preprocessed_tables/dataset1',
                        '0.csv'), sep=',', keep_default_na=False)

    signature = dataset_design.get_pandas_signature(
        cells, {'CD3': '+', 'B2M': '+'})
    computed_sum = sum([1 for entry in signature if entry])
    if computed_sum != 27:
        print('Got computed sum: %s' % computed_sum)
        exit(1)

    signature = dataset_design.get_pandas_signature(
        cells, {'PD1': '+', 'FOXP3': '-', 'CD3': '+'})
    computed_sum = sum([1 for entry in signature if entry])
    if computed_sum != 4:
        print('Got computed sum: %s' % computed_sum)
        exit(1)
