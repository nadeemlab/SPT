"""Source file parsing for metadata at the level of a set of cell manifests."""
from os.path import getsize
import re

import pandas as pd

from \
    spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.halo_cell_metadata_design \
    import HALOCellMetadataDesign
from spatialprofilingtoolbox.workflow.common.file_io import compute_sha256
from spatialprofilingtoolbox.db.source_file_parser_interface import SourceToADIParser
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


def halo_data_type():
    return HALOCellMetadataDesign.get_cell_manifest_descriptor()


def create_specimen_data_measurement_process_record(
    identifier,
    specimen,
    study,
):
    return (identifier, specimen, '', '', study)


class CellManifestSetParser(SourceToADIParser):
    """Parse source files containing metadata at level of cell manifest set."""
    def parse(self, connection, file_manifest_file, study_name):
        """
        Retrieve the set of cell manifests (i.e. just the "metadata" for each source
        file), and parse records for:
        - specimen measurement study
        - specimen data measurement process
        - data file
        """
        file_metadata = pd.read_csv(file_manifest_file, sep='\t')
        cell_manifests = file_metadata[
            file_metadata['Data type'] == halo_data_type()
        ]

        measurement_study = SourceToADIParser.get_measurement_study_name(study_name)

        cursor = connection.cursor()
        cursor.execute(
            self.generate_basic_insert_query('specimen_measurement_study'),
            (measurement_study, 'Multiplexed imaging', '', 'HALO', '', ''),
        )

        for _, cell_manifest in cell_manifests.iterrows():
            logger.debug('Considering "%s" file "%s" .', halo_data_type(), cell_manifest['File ID'])
            sample_id = cell_manifest['Sample ID']
            filename = cell_manifest['File name']
            sha256_hash = compute_sha256(filename)

            measurement_process_identifier = sha256_hash + ' measurement'
            cursor.execute(
                self.generate_basic_insert_query('specimen_data_measurement_process'),
                create_specimen_data_measurement_process_record(
                    measurement_process_identifier,
                    sample_id,
                    measurement_study,
                ),
            )
            match = re.search(r'\.([a-zA-Z0-9]{1,8})$', cell_manifest['File name'])
            if match:
                file_format = match.groups(1)[0].upper()
            else:
                file_format = ''
            cursor.execute(
                self.generate_basic_insert_query('data_file'),
                (
                    sha256_hash,
                    cell_manifest['File name'],
                    file_format,
                    halo_data_type(),
                    getsize(filename),
                    measurement_process_identifier,
                ),
            )
        logger.info('Parsed records for %s cell manifests.', cell_manifests.shape[0])
        connection.commit()
        cursor.close()