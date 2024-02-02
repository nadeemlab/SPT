"""Utility for writing expression matrices in a specially-compressed binary format."""

import json
from os import getcwd

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger


logger = colorized_logger(__name__)


class CompressedMatrixWriter:
    """Write the compressed in-memory binary format matrices to file."""

    def __init__(self, database_config_file: str | None) -> None:
        self.database_config_file = database_config_file

    @classmethod
    def write_specimen(cls, data: dict[int, int], study_name: str, specimen: str) -> None:
        cls._write_data_array(data, study_name, specimen)

    @classmethod
    def _write_data_array(cls,
        data_array: dict[int, int],
        study_name: str,
        specimen: str,
    ) -> None:

        cls._write_data_array_to_db(data_array, study_name, specimen)

    def write_index(self,
        specimens_by_measurement_study: dict[str, list[str]],
        target_index_lookups: dict,
        target_by_symbols: dict,
    ) -> None:
        index = []
        study_names = sorted(list(specimens_by_measurement_study.keys()))
        for study_index, study_name in enumerate(sorted(study_names)):
            index_item: dict[str, str | list] = {}
            index_item['specimen measurement study name'] = study_name
            index_item['target index lookup'] = target_index_lookups[study_name]
            index_item['target by symbol'] = target_by_symbols[study_name]
            index.append(index_item)

            index_str = json.dumps({'': index}, indent=4)
            index_str_as_bytes = index_str.encode('utf-8')

            with DBCursor(database_config_file=self.database_config_file, study=study_name) as cursor:
                insert_query = '''
                    INSERT INTO
                    ondemand_studies_index (
                        specimen,
                        blob_type,
                        blob_contents)
                    VALUES (%s, %s, %s) ;
                    '''
                cursor.execute(insert_query, (specimen, 'expressions_index', index_str_as_bytes))  # check tuple
                cursor.close()

        logger.debug('Wrote expression index to DB %s .')

    @classmethod
    def get_data_directory(cls) -> str:
        return getcwd()

    def _write_data_array_to_db(self, data_array: dict[int, int], study_name: str, specimen: str) -> None:
            blob = bytearray()

            for histological_structure_id, entry in data_array.items():
                blob.append(histological_structure_id.to_bytes(8, 'little'))
                blob.append(entry.to_bytes(8, 'little'))

            with DBCursor(database_config_file=self.database_config_file, study=study_name) as cursor:
                insert_query = '''
                    INSERT INTO
                    ondemand_studies_index (
                        specimen,
                        blob_type,
                        blob_contents)
                    VALUES (%s, %s, %s) ;
                    '''
                cursor.execute(insert_query, (specimen, 'feature_matrix', blob))  # check tuple
                cursor.close()


    def already_exists(self):
        with DBCursor(database_config_file=self.database_config_file) as cursor:
            cursor.execute('''
                    SELECT study_name FROM study_lookup
                    ''')
            studies = tuple(cursor.fetchall())

        for study in studies:
            with DBCursor(database_config_file=self.database_config_file, study=study) as cursor:
                cursor.execute('''
                        SELECT COUNT(*) FROM ondemand_studies_index osi
                        WHERE osi.blob_type='expressions_index';
                        ''')
                count = tuple(cursor.fetchall())[0][0]
                return count > 0

