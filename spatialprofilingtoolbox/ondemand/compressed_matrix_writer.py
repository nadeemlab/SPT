"""Utility for writing expression matrices in a specially-compressed binary format."""

from typing import cast
import json
from os.path import isfile
from os.path import join

from spatialprofilingtoolbox.workflow.common.study_data_arrays import StudyDataArrays
from spatialprofilingtoolbox.ondemand.defaults import EXPRESSIONS_INDEX_FILENAME
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CompressedMatrixWriter:
    """Write the compressed in-memory binary format matrices to file."""

    @classmethod
    def write_study(cls, data_array: StudyDataArrays, study_index: int) -> None:
        cls._write_data_array(data_array, study_index)

    @classmethod
    def _write_data_array(cls, study: StudyDataArrays, study_index: int) -> None:
        specimens = sorted(list(study['data arrays by specimen'].keys()))
        for specimen_index, specimen in enumerate(specimens):
            data_array = study['data arrays by specimen'][specimen]
            filename = '.'.join([
                cls.get_data_array_filename_base(),
                str(study_index),
                str(specimen_index),
                'bin',
            ])
            cls._write_data_array_to_file(cast(dict[int, int], data_array), filename)

    @classmethod
    def write_index(cls,
        specimens_by_measurement_study: dict[str, list[str]],
        target_index_lookups: dict,
        target_by_symbols: dict,
    ) -> None:
        index = []
        study_names = sorted(list(specimens_by_measurement_study.keys()))
        for study_index, study_name in enumerate(sorted(study_names)):
            index_item: dict[str, str | list] = {}
            index_item['specimen measurement study name'] = study_name
            index_item['expressions files'] = []
            specimens = sorted(specimens_by_measurement_study[study_name])
            for specimen_index, specimen in enumerate(specimens):
                filename = '.'.join([
                    cls.get_data_array_filename_base(),
                    str(study_index),
                    str(specimen_index),
                    'bin',
                ])
                index_item['expressions files'].append({
                    'specimen': specimen,
                    'filename': filename,
                })
            index_item['target index lookup'] = target_index_lookups[study_name]
            index_item['target by symbol'] = target_by_symbols[study_name]
            index.append(index_item)
        with open(EXPRESSIONS_INDEX_FILENAME, 'wt', encoding='utf-8') as index_file:
            index_file.write(json.dumps({'': index}, indent=4))
        logger.debug('Wrote expression index file %s .', EXPRESSIONS_INDEX_FILENAME)

    @classmethod
    def _write_data_array_to_file(cls, data_array: dict[int, int], filename: str) -> None:
        with open(filename, 'wb') as file:
            for histological_structure_id, entry in data_array.items():
                file.write(histological_structure_id.to_bytes(8, 'little'))
                file.write(entry.to_bytes(8, 'little'))

    @classmethod
    def already_exists(cls, data_directory: str):
        return isfile(join(data_directory, EXPRESSIONS_INDEX_FILENAME))

    @classmethod
    def get_data_array_filename_base(cls):
        return 'expression_data_array'
