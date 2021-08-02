#!/usr/bin/env python3

import spatialprofilingtoolbox
from spatialprofilingtoolbox.dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign

def shorten(string):
    if len(string) > 30:
        return string[(len(string)-30):len(string)]
    else:
        return string

def test_halo_areas_provider():
    dataset_design = HALOCellMetadataDesign(
        elementary_phenotypes_file = 'data/elementary_phenotypes.csv',
    )
    areas = dataset_design.areas_provider(
        dataset_design=dataset_design,
        regional_areas_file='data/example_areas_file.csv',
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
