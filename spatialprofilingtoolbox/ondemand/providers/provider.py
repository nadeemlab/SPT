"""Base class for on-demand calculation providers."""

from typing import cast
from abc import ABC
from re import search
from os import listdir
from os.path import join
from os.path import isfile
from json import loads

from pandas import DataFrame

from spatialprofilingtoolbox.workflow.common.structure_centroids import StructureCentroids
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class OnDemandProvider(ABC):
    """Base class for OnDemandProvider instances, since they share data ingestion methods."""
    data_arrays: dict[str, dict[str, DataFrame]]

    def __init__(self, data_directory: str, load_centroids: bool = False) -> None:
        """Load expressions from data files and a JSON index file in the data directory."""
        self.load_expressions_indices(data_directory)
        centroids = None
        if load_centroids:
            loader = StructureCentroids()
            loader.load_from_file(data_directory)
            centroids = loader.get_studies()
        self.load_data_matrices(data_directory, centroids)
        logger.info('%s is finished loading source data.', type(self).__name__)

    def load_expressions_indices(self, data_directory: str) -> None:
        """Load expressions metadata from a JSON-formatted index file."""
        logger.debug('Searching for source data in: %s', data_directory)
        json_files = [
            f for f in listdir(data_directory)
            if isfile(join(data_directory, f)) and search(r'\.json$', f)
        ]
        if len(json_files) != 1:
            message = 'Did not find index JSON file.'
            logger.error(message)
            raise FileNotFoundError(message)
        with open(join(data_directory, json_files[0]), 'rt', encoding='utf-8') as file:
            root = loads(file.read())
            entries = root[list(root.keys())[0]]
            self.studies = {}
            for entry in entries:
                self.studies[entry['specimen measurement study name']] = entry

    def load_data_matrices(self, data_directory: str, centroids: dict | None = None) -> None:
        """Load data matrices in reference to a JSON-formatted index file."""
        self.data_arrays = {}
        for study_name in self.get_study_names():
            self.data_arrays[study_name] = {
                item['specimen']: OnDemandProvider.get_data_array_from_file(
                    join(data_directory, item['filename']),
                    self.studies[study_name]['target index lookup'],
                    self.studies[study_name]['target by symbol'],
                )
                for item in self.studies[study_name]['expressions files']
            }
            shapes = [df.shape for df in self.data_arrays[study_name].values()]
            logger.debug('Loaded dataframes of sizes %s ...', shapes[0:5])
            number_specimens = len(self.data_arrays[study_name])
            specimens = list(self.data_arrays[study_name].keys())
            logger.debug('%s specimens loaded (%s ...).', number_specimens, specimens[0:5])
            if centroids is not None:
                for sample, df in self.data_arrays[study_name].items():
                    self.add_centroids(df, centroids, study_name, sample)

    def get_study_names(self) -> list[str]:
        """Retrieve names of the studies held in memory."""
        return list(self.studies.keys())

    @classmethod
    def get_data_array_from_file(
        cls,
        filename: str,
        target_index_lookup: dict,
        target_by_symbol: dict,
    ) -> DataFrame:
        """Load data arrays from a precomputed JSON artifact."""
        rows = []
        target_index_lookup = cast(dict, target_index_lookup)
        target_by_symbol = cast(dict, target_by_symbol)
        feature_columns =  cls.list_columns(target_index_lookup, target_by_symbol)
        size = len(feature_columns)
        with open(filename, 'rb') as file:
            while True:
                buffer = file.read(8)
                row = cls.parse_cell_row(buffer, size)
                if row is None:
                    break
                rows.append(row)
        return DataFrame(rows, columns=feature_columns + ['integer'])

    @staticmethod
    def parse_cell_row(buffer: bytes, size: int) -> tuple[int, ...] | None:
        if buffer == b'':
            return None
        binary_expression_64_string = ''.join([
            ''.join(list(reversed(bin(ii)[2:].rjust(8, '0'))))
            for ii in buffer
        ])
        truncated_to_channels = binary_expression_64_string[0:size]
        integer = int.from_bytes(buffer, 'little')
        return tuple([int(b) for b in list(truncated_to_channels)] + [integer])

    @staticmethod
    def add_centroids(
        df: DataFrame,
        centroids: dict[str, dict[str, list[tuple[float, float]]]],
        study_name: str,
        sample: str,
    ):
        if (centroids is not None) and (study_name is not None) and (sample is not None):
            df['pixel x'] = [point[0] for point in centroids[study_name][sample]]
            df['pixel y'] = [point[1] for point in centroids[study_name][sample]]

    @staticmethod
    def list_columns(target_index_lookup: dict, target_by_symbol: dict) -> list[str]:
        target_by_index = {
            value: key for key, value in target_index_lookup.items()
        }
        symbol_by_target = {
            value: key for key, value in target_by_symbol.items()
        }
        return [
            symbol_by_target[target_by_index[i]]
            for i in range(len(target_by_index))
        ]
