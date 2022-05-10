#!/usr/bin/env python3
import os
from os.path import join
from os.path import dirname

import pandas as pd

import spatialprofilingtoolbox
from spatialprofilingtoolbox.environment.configuration_settings import elementary_phenotypes_file_identifier
from spatialprofilingtoolbox.environment.file_io import get_input_filename_by_identifier
from spatialprofilingtoolbox.dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign
from spatialprofilingtoolbox.workflows.phenotype_proximity.core import PhenotypeProximityCalculator
from spatialprofilingtoolbox.workflows.phenotype_proximity.computational_design import PhenotypeProximityDesign
from spatialprofilingtoolbox.environment.source_file_parsers.skimmer import DataSkimmer
import spatialprofilingtoolbox as spt


def test_data_skimmer():
    """
    To activate the main feature of this test, set environment variables:

    PATHSTUDIES_DB_ENDPOINT
    PATHSTUDIES_DB_USER
    PATHSTUDIES_DB_PASSWORD
    """
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
    with DataSkimmer(
        dataset_design = dataset_design,
        input_path = input_files_path,
        file_manifest_file = file_manifest_file,
    ) as skimmer:
        skimmer.parse()


if __name__=='__main__':
    test_data_skimmer()

