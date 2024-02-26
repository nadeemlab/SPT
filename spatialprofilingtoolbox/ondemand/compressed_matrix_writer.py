"""Utility for writing expression matrices in a specially-compressed binary format."""

from typing import cast
import json

from spatialprofilingtoolbox.db.ondemand_studies_index import get_counts
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import retrieve_primary_study
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CompressedMatrixWriter:
    """Write the compressed in-memory binary format matrices to file."""
    database_config_file: str

    def __init__(self, database_config_file: str | None) -> None:
        self.database_config_file = cast(str, database_config_file)

    def write_specimen(self, data: dict[int, int], study_name: str, specimen: str) -> None:
        self._write_data_array(data, study_name, specimen)

    def _write_data_array(self,
        data_array: dict[int, int],
        study_name: str,
        specimen: str,
    ) -> None:
        self._write_data_array_to_db(data_array, study_name, specimen)

    def write_index(self,
        specimens_by_measurement_study: dict[str, list[str]],
        target_index_lookups: dict,
        target_by_symbols: dict,
    ) -> None:
        study_names = sorted(list(specimens_by_measurement_study.keys()))
        for measurement_study_name in sorted(study_names):
            index_item: dict[str, str | list] = {}
            index_item['specimen measurement study name'] = measurement_study_name
            index_item['target index lookup'] = target_index_lookups[measurement_study_name]
            index_item['target by symbol'] = target_by_symbols[measurement_study_name]
            index_str = json.dumps({'': [index_item]})
            index_str_as_bytes = index_str.encode('utf-8')
            study = retrieve_primary_study(self.database_config_file, measurement_study_name)
            with DBCursor(database_config_file=self.database_config_file, study=study) as cursor:
                insert_query = '''
                    INSERT INTO
                    ondemand_studies_index (
                        specimen,
                        blob_type,
                        blob_contents
                    )
                    VALUES (%s, %s, %s) ;
                '''
                cursor.execute(insert_query, (None, 'expressions_index', index_str_as_bytes))
                cursor.close()
            logger.debug(f'Wrote expression index to database {study} .')

    def _write_data_array_to_db(
        self,
        data_array: dict[int, int],
        measurement_study_name: str,
        specimen: str,
    ) -> None:
        blob = bytearray()
        for histological_structure_id, entry in data_array.items():
            blob.extend(histological_structure_id.to_bytes(8, 'little'))
            blob.extend(entry.to_bytes(8, 'little'))
        study_name = retrieve_primary_study(self.database_config_file, measurement_study_name)
        with DBCursor(database_config_file=self.database_config_file, study=study_name) as cursor:
            insert_query = '''
                INSERT INTO
                ondemand_studies_index (
                    specimen,
                    blob_type,
                    blob_contents)
                VALUES (%s, %s, %s) ;
            '''
            cursor.execute(insert_query, (specimen, 'feature_matrix', blob))
            cursor.close()

    def expressions_indices_already_exist(self, study: str | None = None):
        counts = get_counts(self.database_config_file, 'expressions_index', study=study)
        for _study, count in counts.items():
            if count > 1:
                message = f'Too many ({count}) expression index files for study {_study}.'
                raise ValueError(message)
        return all(count == 1 for count in counts.values())
