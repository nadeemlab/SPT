import os
from os.path import getsize
from os.path import join
import re

import pandas as pd

from ..dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign
from ..common.file_io import compute_sha256
from ...db.source_file_parser_interface import SourceToADIParser
from ...standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)


class CellManifestSetParser(SourceToADIParser):
    def __init__(self, **kwargs):
        super(CellManifestSetParser, self).__init__(**kwargs)

    def parse(self, connection, fields, file_manifest_file):
        """
        Retrieve the set of cell manifests (i.e. just the "metadata" for each source
        file), and parse records for:
        - specimen measurement study
        - specimen data measurement process
        - data file
        """
        file_metadata = pd.read_csv(file_manifest_file, sep='\t')
        halo_data_type = HALOCellMetadataDesign.get_cell_manifest_descriptor()
        cell_manifests = file_metadata[
            file_metadata['Data type'] == halo_data_type
        ]

        def create_specimen_data_measurement_process_record(
            identifier,
            specimen,
            study,
        ):
            return (identifier, specimen, '', '', study)

        def create_data_file_record(
            sha256_hash,
            file_name,
            file_format,
            contents_format,
            size,
            source_generation_process,
        ):
            return (
                sha256_hash,
                file_name,
                file_format,
                contents_format,
                size,
                source_generation_process,
            )

        project_handles = sorted(list(set(file_metadata['Project ID']).difference([''])))
        if len(project_handles) == 0:
            message = 'No "Project ID" values are supplied with the file manifest for this run.'
            logger.error(message)
            raise ValueError(message)
        if len(project_handles) > 1:
            message = 'Multiple "Project ID" values were supplied with the file manifest for this run. Using "%s".' % project_handles[0]
            logger.warning(message)
        project_handle = project_handles[0]
        measurement_study = project_handle + ' - measurement'

        cursor = connection.cursor()
        cursor.execute(
            self.generate_basic_insert_query('specimen_measurement_study', fields),
            (measurement_study, 'Multiplexed imaging', '', 'HALO', '', ''),
        )

        for i, cell_manifest in cell_manifests.iterrows():
            logger.debug('Considering "%s" file "%s" .', halo_data_type, cell_manifest['File ID'])
            sample_id = cell_manifest['Sample ID']
            filename = cell_manifest['File name']
            sha256_hash = compute_sha256(filename)

            measurement_process_identifier = sha256_hash + ' measurement'
            cursor.execute(
                self.generate_basic_insert_query('specimen_data_measurement_process', fields),
                create_specimen_data_measurement_process_record(
                    measurement_process_identifier,
                    sample_id,
                    measurement_study,
                ),
            )
            match = re.search('\.([a-zA-Z0-9]{1,8})$', cell_manifest['File name'])
            if match:
                file_format = match.groups(1)[0].upper()
            else:
                file_format = ''
            size = getsize(filename)
            cursor.execute(
                self.generate_basic_insert_query('data_file', fields),
                create_data_file_record(
                    sha256_hash,
                    cell_manifest['File name'],
                    file_format,
                    halo_data_type,
                    size,
                    measurement_process_identifier,
                ),
            )
        logger.info('Parsed records for %s cell manifests.', cell_manifests.shape[0])
        connection.commit()
        cursor.close()
