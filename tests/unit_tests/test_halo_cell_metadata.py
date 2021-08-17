#!/usr/bin/env python3
import os
from os.path import join, dirname

import spatialprofilingtoolbox
from spatialprofilingtoolbox.dataset_designs.multiplexed_imaging.halo_cell_metadata_provider import HALOCellMetadata
from spatialprofilingtoolbox.dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign

def test_halo_load_cell_metadata():
    assert False

    input_files_path = join(dirname(__file__), '..', 'data')
    elementary_phenotypes_file = join(input_files_path, 'elementary_phenotypes.csv')
    file_manifest_file = join(input_files_path, 'file_manifest.tsv')
    dataset_design = HALOCellMetadataDesign(
        elementary_phenotypes_file=elementary_phenotypes_file,
    )
    m = HALOCellMetadata(
        input_files_path = input_files_path,
        dataset_design = dataset_design,
        file_manifest_file = file_manifest_file,
    )
    m.initialize()

    outcomes_file = join(input_files_path, 'diagnosis.tsv')
    m.write_subsampled(max_per_sample = 10, outcomes_file = outcomes_file)
    m.write_subsampled(max_per_sample = 20, outcomes_file = outcomes_file, omit_column='DAPI')

if __name__=='__main__':
    test_halo_load_cell_metadata()
