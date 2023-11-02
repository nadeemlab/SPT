"""Base class for on-demand calculation providers."""

from typing import (
    cast,
    Any,
)
from abc import ABC
from re import search
from os import listdir
from os.path import join
from os.path import isfile
from json import loads
from warnings import warn

from pandas import DataFrame

from spatialprofilingtoolbox.workflow.common.structure_centroids import (
    StructureCentroids,
    StudyStructureCentroids,
)
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class OnDemandProvider(ABC):
    """Base class for OnDemandProvider instances, since they share data ingestion methods."""
    data_arrays: dict[str, dict[str, DataFrame]]
    timeout: int
    timeouts: dict[tuple[str, str], float]

    @classmethod
    def service_specifier(cls) -> str:
        raise NotImplementedError

    def __init__(self, data_directory: str, timeout: int, load_centroids: bool = False) -> None:
        """Load expressions from data files and a JSON index file in the data directory."""
        self._load_expressions_indices(data_directory)
        self.timeout = timeout
        self.timeouts = {}
        centroids = None
        if load_centroids:
            loader = StructureCentroids()
            loader.set_data_directory(data_directory)
            loader.load_from_file()
            centroids = loader.get_studies()
        self._load_data_matrices(data_directory, centroids)
        logger.info('%s is finished loading source data.', type(self).__name__)

    def _load_expressions_indices(self, data_directory: str) -> None:
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

    def _load_data_matrices(
        self,
        data_directory: str,
        centroids: dict[str, StudyStructureCentroids] | None = None,
    ) -> None:
        """Load data matrices in reference to a JSON-formatted index file."""
        self.data_arrays = {}
        for study_name in self._get_study_names():
            self.data_arrays[study_name] = {
                item['specimen']: OnDemandProvider._get_data_array_from_file(
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
                    self._add_centroids(df, centroids, study_name, sample)

    def _get_study_names(self) -> list[str]:
        """Retrieve names of the studies held in memory."""
        return list(self.studies.keys())

    @classmethod
    def _get_data_array_from_file(
        cls,
        filename: str,
        target_index_lookup: dict,
        target_by_symbol: dict,
    ) -> DataFrame:
        """Load data arrays from a precomputed binary artifact."""
        rows = []
        target_index_lookup = cast(dict, target_index_lookup)
        target_by_symbol = cast(dict, target_by_symbol)
        feature_columns = cls._list_columns(target_index_lookup, target_by_symbol)
        size = len(feature_columns)
        with open(filename, 'rb') as file:
            while True:
                buffer1 = file.read(8)
                buffer2 = file.read(8)
                row = cls._parse_cell_row(buffer1, buffer2, size)
                if row is None:
                    break
                rows.append(row)
        df = DataFrame(rows, columns=feature_columns + ['integer', 'histological_structure_id'])
        df.set_index('histological_structure_id', inplace=True)
        return df

    @staticmethod
    def _parse_cell_row(buffer1: bytes, buffer2: bytes, size: int) -> tuple[int, ...] | None:
        if buffer1 == b'':
            return None
        binary_expression_64_string = ''.join([
            ''.join(list(reversed(bin(ii)[2:].rjust(8, '0'))))
            for ii in buffer2
        ])
        truncated_to_channels = binary_expression_64_string[0:size]
        int_phenotypes = int.from_bytes(buffer2, 'little')
        int_id = int.from_bytes(buffer1, 'little')
        return tuple([int(b) for b in list(truncated_to_channels)] + [int_phenotypes] + [int_id])

    @staticmethod
    def _add_centroids(
        df: DataFrame,
        centroids: dict[str, StudyStructureCentroids],
        study_name: str,
        sample: str,
    ) -> None:
        coordinates = ['pixel x', 'pixel y']
        location_data = DataFrame.from_dict(centroids[study_name][sample], orient='index')
        if location_data.shape[0] != df.shape[0]:
            present = location_data.shape[0]
            before = df.shape[0]
            message = f'Can not add location data {present} to feature matrix with {before} rows.'
            logger.error(message)
        df[coordinates] = location_data

    @staticmethod
    def _list_columns(target_index_lookup: dict, target_by_symbol: dict) -> list[str]:
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

    def get_status(self) -> list[dict[str, Any]]:
        """Get the status of all studies."""
        warn(f'{type(self).__name__}.get_status() not implemented. Returning empty response.')
        return []

    def has_study(self, study_name: str) -> bool:
        """Check if this study is available in this provider."""
        return study_name in self.studies
