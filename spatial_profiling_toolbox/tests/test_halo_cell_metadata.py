#!/usr/bin/env python3
import os
from os.path import join

import spatial_profiling_toolbox
from spatial_profiling_toolbox.dataset_designs.multiplexed_immunofluorescence.halo_cell_metadata_provider import HALOCellMetadata
from spatial_profiling_toolbox.dataset_designs.multiplexed_immunofluorescence.halo_cell_metadata_design import HALOCellMetadataDesign

def test_halo_load_cell_metadata():
    input_files_path = 'data/'
    file_manifest_file = 'data/file_manifest.tsv'
    md_path = 'data/'
    dataset_design = HALOCellMetadataDesign(
        elementary_phenotypes_file=join(md_path, 'elementary_phenotypes.csv'),
    )
    m = HALOCellMetadata(
        input_files_path = input_files_path,
        dataset_design = dataset_design,
        file_manifest_file = file_manifest_file,
    )
    m.initialize()

if __name__=='__main__':
    test_halo_load_cell_metadata()
