#!/usr/bin/env python3
import os
from os.path import join, dirname

os.environ['FIND_FILES_USING_PATH'] = '1'

import spatialprofilingtoolbox
from spatialprofilingtoolbox.dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign

def shorten(string):
    if len(string) > 30:
        return string[(len(string)-30):len(string)]
    else:
        return string

def test_halo_areas_provider():
    input_files_path = join(dirname(__file__), '..', 'data')
    file_manifest_file = 'file_manifest.tsv'
    dataset_design = HALOCellMetadataDesign(
        input_path = input_files_path,
        file_manifest_file = file_manifest_file,
        compartments=['Tumor','Non-Tumor'],
    )
    regional_areas_file = 'example_areas_file.csv'
    areas = dataset_design.areas_provider(
        dataset_design=dataset_design,
        regional_areas_file=regional_areas_file,
    )
    print('FOV                            Compartment          Area       Units')
    print('--------------------------------------------------------------------')
    for fov, compartment in areas.get_fov_compartments():
        print(shorten(fov), end=' ',)
        print(compartment.ljust(20), end=' ',)
        area = areas.get_area(fov=fov, compartment=compartment)
        print(str(area).ljust(10) + ' ' + areas.get_units(compartment), end=' ',)
        print('')


if __name__=='__main__':
    test_halo_areas_provider()
