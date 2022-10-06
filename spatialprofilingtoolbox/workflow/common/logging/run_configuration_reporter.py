import os
from os.path import getsize
import datetime
import socket

import pandas as pd

from ...dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign
from ....standalone_utilities.configuration_settings import get_version
from ....standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)


class RunConfigurationReporter:
    def __init__(
        self,
        workflow: str=None,
        file_manifest_file: str=None,
        outcomes_file: str=None,
        elementary_phenotypes_file: str=None,
        composite_phenotypes_file: str=None,
        compartments_file: str=None,
    ):
        logger.info('Machine host: %s', socket.gethostname())
        logger.info('Version: SPT v%s', get_version())
        logger.info('Workflow: "%s"', workflow)

        file_metadata = pd.read_csv(file_manifest_file, sep='\t', keep_default_na=False)
        project_handle = sorted(list(set(file_metadata['Project ID']).difference([''])))[0]
        if project_handle != '':
            logger.info('Dataset/project: "%s"', project_handle)
            current = datetime.datetime.now()
            year = current.date().strftime("%Y")
            logger.info('Run date year: %s', year)

        sizes = self.retrieve_cell_manifest_sizes(file_manifest_file)
        logger.info('Number of cell manifest files: %s', len(sizes))
        logger.info('Total cell manifest file size: %s MB', self.format_mb(sum(sizes)))
        logger.info('Smallest cell manifest: %s MB', self.format_mb(min(sizes)))
        logger.info('Largest cell manifest: %s MB', self.format_mb(max(sizes)))

        if outcomes_file:
            outcomes = pd.read_csv(outcomes_file, sep='\t', keep_default_na=False, dtype=str)
        else:
            sample_ids = self.retrieve_cell_manifest_sample_identifiers(file_manifest_file)
            outcomes = pd.DataFrame({
                'Sample ID' : sample_ids,
                'Outcome' : ['Unknown outcome assignment' for i in sample_ids],
            })[['Sample ID', 'Outcome']]
        labels = sorted(list(set(outcomes[outcomes.columns[1]])))

        elementary_phenotypes = pd.read_csv(elementary_phenotypes_file, keep_default_na=False)
        composite_phenotypes = pd.read_csv(composite_phenotypes_file, keep_default_na=False)
        channels = sorted(list(set(elementary_phenotypes['Name'])))
        compartments = open(compartments_file, 'rt').read().rstrip('\n').split('\n')

        logger.info('Number of outcome labels: %s', len(labels))
        logger.info('Number of channels: %s', elementary_phenotypes.shape[0])
        logger.info('Number of phenotypes considered: %s', composite_phenotypes.shape[0])
        logger.info('Number of compartments: %s', len(compartments))
        logger.info('Outcomes: %s', '; '.join(labels))
        logger.info('Outcome frequencies: %s', self.get_frequencies(outcomes))
        logger.info('Channels: %s', '; '.join(channels))
        logger.info('Compartments: %s', '; '.join(compartments))

    def get_frequencies(self, outcomes):
        column = outcomes[outcomes.columns[1]]
        labels = sorted(list(set(column)))
        return { label : sum([1 for value in column if value == label]) for label in labels}

    def format_mb(self, number_bytes):
        return int(10 * number_bytes / 1000000) / 10

    def retrieve_cell_manifest_sizes(self, file_manifest_file):
        validate = HALOCellMetadataDesign.validate_cell_manifest_descriptor
        return [
            getsize(row['File name'])
            for i, row in pd.read_csv(file_manifest_file, sep='\t').iterrows()
            if validate(row['Data type'])
        ]

    def retrieve_cell_manifest_sample_identifiers(self, file_manifest_file):
        validate = HALOCellMetadataDesign.validate_cell_manifest_descriptor
        return [
            row['Sample ID']
            for i, row in pd.read_csv(file_manifest_file, sep='\t').iterrows()
            if validate(row['Data type'])
        ]
