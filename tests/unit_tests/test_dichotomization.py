#!/usr/bin/env python3
import os
from os.path import join, dirname
import warnings

os.environ['FIND_FILES_USING_PATH'] = '1'

import pandas as pd
import pytest

import spatialprofilingtoolbox
from spatialprofilingtoolbox.environment.configuration_settings import elementary_phenotypes_file_identifier
from spatialprofilingtoolbox.environment.file_io import get_input_filename_by_identifier
from spatialprofilingtoolbox.environment.dichotomization import Dichotomizer
from spatialprofilingtoolbox.dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign

@pytest.mark.filterwarnings("error::sklearn.exceptions.ConvergenceWarning")
def test_thresholding():
    input_files_path = join(dirname(__file__), '..', 'data_compartments_explicit')
    file_manifest_file = join(input_files_path, 'file_manifest.tsv')
    dataset_design = HALOCellMetadataDesign(
        elementary_phenotypes_file = join(
            input_files_path,
            get_input_filename_by_identifier(
                elementary_phenotypes_file_identifier,
                file_manifest_filename = file_manifest_file,
            ),
        ),
        compartments_file = join(
            input_files_path,
            get_input_filename_by_identifier(
                'Compartments file',
                file_manifest_filename = file_manifest_file,
            ),
        )
    )
    file_manifest = pd.read_csv(file_manifest_file, sep='\t')
    cell_manifest = HALOCellMetadataDesign.get_cell_manifest_descriptor()
    input_files = file_manifest[file_manifest['Data type'] == cell_manifest]['File name']
    for filename in input_files:
        cells = pd.read_csv(join(input_files_path, filename))
        rows = []
        for phenotype in dataset_design.get_elementary_phenotype_names():
            dataset_design.add_combined_intensity_column(cells, phenotype)
            feature = dataset_design.get_feature_name(phenotype)
            known_number_positives = sum(cells[feature])
            Dichotomizer.dichotomize(
                phenotype,
                cells,
                dataset_design=dataset_design,
                enable_overwrite_warning=False,
            )
            new_number_positives = sum(cells[feature])
            row = {
                'Phenotype' : phenotype,
                'Previous' : known_number_positives,
                'Thresholded' : new_number_positives,
            }
            rows.append(row)
        print('')
        print('In file %s' % filename)
        print(pd.DataFrame(rows))

if __name__=='__main__':
    test_thresholding()
