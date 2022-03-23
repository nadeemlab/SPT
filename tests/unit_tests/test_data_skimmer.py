#!/usr/bin/env python3
import os
from os.path import join
from os.path import dirname
os.environ['FIND_FILES_USING_PATH'] = '1'

import pandas as pd

import spatialprofilingtoolbox
from spatialprofilingtoolbox.environment.settings_wrappers import DatasetSettings
from spatialprofilingtoolbox.dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign
from spatialprofilingtoolbox.workflows.phenotype_proximity.core import PhenotypeProximityCalculator
from spatialprofilingtoolbox.workflows.phenotype_proximity.computational_design import PhenotypeProximityDesign
from spatialprofilingtoolbox.environment.configuration import get_config_parameters
from spatialprofilingtoolbox.environment.skimmer import DataSkimmer
import spatialprofilingtoolbox as spt


def test_data_skimmer():
    """
    To activate the main feature of this test, set environment variables:

    PATHSTUDIES_DB_ENDPOINT
    PATHSTUDIES_DB_USER
    PATHSTUDIES_DB_PASSWORD
    """
    spt_pipeline_json = open('./unit_tests/proximity_skimming.json', 'rt').read()
    parameters = spt.get_config_parameters(json_string=spt_pipeline_json)

    input_files_path = join(dirname(__file__), '..', 'data')
    file_manifest_file = 'file_manifest.tsv'
    dataset_design = HALOCellMetadataDesign(
        input_path = input_files_path,
        file_manifest_file = file_manifest_file,
        compartments = parameters['compartments'],
    )
    file_manifest = pd.read_csv(join(input_files_path, file_manifest_file), sep='\t')
    dataset_settings = DatasetSettings(
        input_files_path,
        file_manifest_file,
    )
    if 'PATHSTUDIES_DB_ENDPOINT' in os.environ:
        endpoint = os.environ['PATHSTUDIES_DB_ENDPOINT']
        user = os.environ['PATHSTUDIES_DB_USER']
        password = os.environ['PATHSTUDIES_DB_PASSWORD']
        with DataSkimmer(
            endpoint=endpoint,
            user=user,
            password=password,
            dataset_settings=dataset_settings,
            dataset_design=dataset_design,
        ) as skimmer:
            skimmer.skim_initial_data()


if __name__=='__main__':
    test_data_skimmer()
