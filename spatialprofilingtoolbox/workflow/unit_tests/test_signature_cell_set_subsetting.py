import os
from os.path import join

import pandas as pd

import spatialprofilingtoolbox
from spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign

if __name__=='__main__':
    dataset_design = HALOCellMetadataDesign(
        elementary_phenotypes_file = join('..', 'test_data', 'adi_preprocessed_tables', 'elementary_phenotypes.csv'),
    )
    cells = pd.read_csv(join('..', 'test_data', 'adi_preprocessed_tables', 'lesion_0_1.csv'), sep=',', keep_default_na=False)

    signature = dataset_design.get_pandas_signature(cells, {'CD3' : '+', 'B2M' : '+'})
    computed_sum = sum([1 for entry in signature if entry])
    if computed_sum != 27:
        print('Got computed sum: %s' % computed_sum)
        exit(1)

    signature = dataset_design.get_pandas_signature(cells, {'PD1' : '+', 'FOXP3' : '-', 'CD3' : '+'})
    computed_sum = sum([1 for entry in signature if entry])
    if computed_sum != 4:
        print('Got computed sum: %s' % computed_sum)
        exit(1)
