import os
from os.path import getsize
import re

import pandas as pd

from ..file_io import get_input_filename_by_identifier
from ..file_io import compute_sha256
from .parser import SourceFileSemanticParser
from ..log_formats import colorized_logger
logger = colorized_logger(__name__)


class CellManifestSetParser(SourceFileSemanticParser):
    def __init__(self, **kwargs):
        super(CellManifestSetParser, self).__init__(**kwargs)

    def parse(self, connection, fields, dataset_settings, dataset_design):
        """
        Retrieve the set of cell manifests (i.e. just the "metadata" for each source
        file), and parse records for:
        - specimen collection study
        - specimen collection process
        - specimen measurement study
        - specimen data measurement process
        - data file
        """
        file_metadata = pd.read_csv(dataset_settings.file_manifest_file, sep='\t')
        halo_data_type = 'HALO software cell manifest'
        cell_manifests = file_metadata[
            file_metadata['Data type'] == halo_data_type
        ]

        def create_specimen_collection_process_record(specimen, source, study):
            return (specimen, source, '', '', '', study)

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
        collection_study = project_handle + ' - specimen collection'
        measurement_study = project_handle + ' - measurement'

        cursor = connection.cursor()
        cursor.execute(
            self.generate_basic_insert_query('specimen_collection_study', fields),
            (collection_study, '', '', '', '', ''),
        )
        cursor.execute(
            self.generate_basic_insert_query('specimen_measurement_study', fields),
            (measurement_study, 'Multiplexed imaging', '', 'HALO', '', ''),
        )

        for i, cell_manifest in cell_manifests.iterrows():
            logger.debug('Considering "%s" file "%s" .', halo_data_type, cell_manifest['File ID'])
            subject_id = cell_manifest['Sample ID']
            subspecimen_identifier = subject_id + ' subspecimen'
            cursor.execute(
                self.generate_basic_insert_query('specimen_collection_process', fields),
                create_specimen_collection_process_record(
                    subspecimen_identifier,
                    subject_id,
                    collection_study,
                ),
            )
            filename = get_input_filename_by_identifier(
                dataset_settings = dataset_settings,
                input_file_identifier = cell_manifest['File ID'],
            )
            sha256_hash = compute_sha256(filename)

            if 'SHA256' in cell_manifests.columns:
                if sha256_hash != cell_manifest['SHA256']:
                    logger.warning(
                        'Computed hash "%s" does not match hash supplied in file manifest, "%s", for file "%s".',
                        sha256_hash,
                        cell_manifest['SHA256'],
                        cell_manifest['File ID'],
                    )

            measurement_process_identifier = sha256_hash + ' measurement'
            cursor.execute(
                self.generate_basic_insert_query('specimen_data_measurement_process', fields),
                create_specimen_data_measurement_process_record(
                    measurement_process_identifier,
                    subspecimen_identifier,
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
