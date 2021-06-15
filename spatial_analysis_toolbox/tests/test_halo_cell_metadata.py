#!/usr/bin/env python3
import os
from os.path import join

import spatial_analysis_toolbox
from spatial_analysis_toolbox.dataset_designs.multiplexed_immunofluorescence.halo_cell_metadata_provider import HALOCellMetadata
from spatial_analysis_toolbox.dataset_designs.multiplexed_immunofluorescence.halo_cell_metadata_design import HALOCellMetadataDesign

def test_halo_load_cell_metadata():
    input_files_path = 'data/colon/'
    file_manifest_file = 'data/colon/file_manifest.tsv'
    md_path = '../../project_data_and_metadata/colon_msi/'
    dataset_design = HALOCellMetadataDesign(
        elementary_phenotypes_file=join(md_path, 'elementary_phenotypes.csv'),
    )
    m = HALOCellMetadata(
        input_files_path = input_files_path,
        input_data_design = data_design,
        file_manifest_file = file_manifest_file,
    )
    m.initialize()

if __name__=='__main__':
    test_halo_load_cell_metadata()
