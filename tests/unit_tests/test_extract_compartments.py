#!/usr/bin/env python3
import os
from os.path import join
from os.path import dirname

import spatialprofilingtoolbox
from spatialprofilingtoolbox.environment.file_io import get_input_filenames_by_data_type
from spatialprofilingtoolbox.dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign
from spatialprofilingtoolbox.environment.extract_compartments import extract_compartments

def test_extract_compartments():
    compartments = extract_compartments( #input_path=join(dirname(__file__), '..', 'data'), file_manifest_file='file_manifest.tsv',
        [
            join('./data', f)
            for f in get_input_filenames_by_data_type(
                data_type=HALOCellMetadataDesign.get_cell_manifest_descriptor(),
                file_manifest_filename=join('./data', 'file_manifest.tsv'),
            )
        ]
    )

    if not compartments:
        raise ValueError(
            '"compartments" not generated at all.'
        )
    else:
        if compartments == []:
            raise ValueError('Compartments list empty, not extracted.')
        else:
            if compartments != ['Non-Tumor', 'Stroma', 'Tumor']:
                raise ValueError('Compartments list not exactly as expected.')


if __name__=='__main__':
    test_extract_compartments()
