#!/usr/bin/env python3
import os
from os.path import join
from os.path import dirname
os.environ['FIND_FILES_USING_PATH'] = '1'

import pandas as pd

import spatialprofilingtoolbox
from spatialprofilingtoolbox.dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign
from spatialprofilingtoolbox.workflows.phenotype_proximity.core import PhenotypeProximityCalculator
from spatialprofilingtoolbox.workflows.phenotype_proximity.computational_design import PhenotypeProximityDesign
from spatialprofilingtoolbox.environment.skimmer import DataSkimmer
import spatialprofilingtoolbox as spt


def test_data_skimmer():
    """
    To activate the main feature of this test, set environment variables:

    PATHSTUDIES_DB_ENDPOINT
    PATHSTUDIES_DB_USER
    PATHSTUDIES_DB_PASSWORD
    """
    input_files_path = join(dirname(__file__), '..', 'data')
    file_manifest_file = 'file_manifest.tsv'
    dataset_design = HALOCellMetadataDesign(
        input_path = input_files_path,
        file_manifest_file = file_manifest_file,
        compartments = ['Tumor', 'Non-Tumor'],
    )
    file_manifest = pd.read_csv(join(input_files_path, file_manifest_file), sep='\t')
    with DataSkimmer(
        dataset_design=dataset_design,
    ) as skimmer:
        skimmer.parse()

def test_data_skimmer_incomplete_credentials():
    input_files_path = join(dirname(__file__), '..', 'data')
    file_manifest_file = 'file_manifest.tsv'
    dataset_design = HALOCellMetadataDesign(
        input_path = input_files_path,
        file_manifest_file = file_manifest_file,
        compartments = ['Tumor', 'Non-Tumor'],
    )
    file_manifest = pd.read_csv(join(input_files_path, file_manifest_file), sep='\t')
    credential_parameters = [
        'PATHSTUDIES_DB_ENDPOINT',
        'PATHSTUDIES_DB_USER',
        'PATHSTUDIES_DB_PASSWORD',
    ]
    cached = {}
    for c in credential_parameters:
        if c in os.environ:
            cached[c] = os.environ[c]
            del os.environ[c]
    os.environ['PATHSTUDIES_DB_ENDPOINT'] = ''
    try:
        with DataSkimmer(
            dataset_design=dataset_design,
        ) as skimmer:
            skimmer.parse()
        raise Exception('Incomplete credentials not caught.')
    except EnvironmentError:
        for c in os.environ:
            if c in cached:
                os.environ[c] = cached[c]
            else:
                del os.environ[c]


if __name__=='__main__':
    test_data_skimmer_incomplete_credentials()
    test_data_skimmer()

