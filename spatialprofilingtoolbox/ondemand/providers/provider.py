"""Base class for on-demand calculation providers."""

from typing import cast
from typing import Any
from abc import ABC
from json import loads
from warnings import warn

from pandas import DataFrame

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import retrieve_study_names
from spatialprofilingtoolbox.db.database_connection import retrieve_primary_study
from spatialprofilingtoolbox.workflow.common.structure_centroids import (
    StructureCentroids,
    StudyStructureCentroids,
)
from spatialprofilingtoolbox.workflow.common.sparse_matrix_puller import SparseMatrixPuller
from spatialprofilingtoolbox.db.ondemand_studies_index import retrieve_expressions_index
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class OnDemandProvider(ABC):
    """Base class for OnDemandProvider instances, since they share data ingestion methods."""
    data_arrays: dict[str, dict[str, DataFrame]]
    timeout: int
    timeouts: dict[tuple[str, str], float]
    database_config_file: str

    @classmethod
    def service_specifier(cls) -> str:
        raise NotImplementedError

    def __init__(self, timeout: int, database_config_file: str | None, load_centroids: bool = False) -> None:
        """Load expressions from data files and a JSON index file in the data directory."""
        self.database_config_file = cast(str, database_config_file)
        self._load_expressions_indices()
        self.timeout = timeout
        self.timeouts = {}
        centroids = None
        if load_centroids:
            loader = StructureCentroids(database_config_file)
            loader.load_from_db()
            centroids = loader.get_studies()
        self._load_data_matrices(centroids=centroids)
        logger.info('%s is finished loading source data.', type(self).__name__)

    def _load_expressions_indices(self) -> None:
        """Load expressions metadata from a JSON-formatted index file."""
        logger.debug('Searching for source data in database')
        self.studies = {}
        for study_name in retrieve_study_names(self.database_config_file):
            get_index = retrieve_expressions_index
            decoded_blob = get_index(self.database_config_file, study_name)
            decoded_blob = cast(str, decoded_blob)
            root = loads(decoded_blob)
            entries = root[list(root.keys())[0]]
            for entry in entries:
                self.studies[entry['specimen measurement study name']] = entry

    def _load_data_matrices(
        self,
        centroids: dict[str, StudyStructureCentroids] | None = None,
    ) -> None:
        """Load data matrices in reference to a JSON-formatted index file."""
        self.data_arrays = {}
        for measurement_study_name in self._get_study_names():
            study = cast(str, retrieve_primary_study(
                self.database_config_file, measurement_study_name
            ))
            pertinent_specimens = SparseMatrixPuller.get_pertinent_specimens(
                self.database_config_file,
                study,
                measurement_study_name,
                None,
            )
            self.data_arrays[measurement_study_name] = {
                specimen: self._get_data_array_from_db(
                    specimen,
                    self.studies[measurement_study_name]['target index lookup'],
                    self.studies[measurement_study_name]['target by symbol'],
                    study,
                )
                for specimen in pertinent_specimens
            }
            shapes = [df.shape for df in self.data_arrays[measurement_study_name].values()]
            logger.debug('Loaded dataframes of sizes %s ...', shapes[0:5])
            number_specimens = len(self.data_arrays[measurement_study_name])
            specimens = list(self.data_arrays[measurement_study_name].keys())
            logger.debug('%s specimens loaded (%s ...).', number_specimens, specimens[0:5])
            if centroids is not None:
                for sample, df in self.data_arrays[measurement_study_name].items():
                    self._add_centroids(df, centroids, measurement_study_name, sample)

    def _get_study_names(self) -> list[str]:
        """Retrieve names of the studies held in memory."""
        return list(self.studies.keys())

    def _get_data_array_from_db(
        self,
        specimen: str,
        target_index_lookup: dict,
        target_by_symbol: dict,
        study_name: str,
    ) -> DataFrame:
        """Load data arrays from a precomputed blob from database."""
        with DBCursor(database_config_file=self.database_config_file, study=study_name) as cursor:
            cursor.execute('''
                SELECT blob_contents FROM ondemand_studies_index osi
                WHERE osi.specimen=%s AND osi.blob_type='feature_matrix';
            ''', (specimen,))
            result_blob = bytearray(tuple(cursor.fetchall())[0][0])
        rows = []
        target_index_lookup = cast(dict, target_index_lookup)
        target_by_symbol = cast(dict, target_by_symbol)
        feature_columns = self._list_columns(target_index_lookup, target_by_symbol)
        size = len(feature_columns)
        if result_blob is not None:
            increment = 0
            while True:
                buffer1 = result_blob[increment: increment + 8]
                buffer2 = result_blob[increment + 8: increment + 16]
                increment += 16
                row = self._parse_cell_row(buffer1, buffer2, size)
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

    def _add_centroids(
        self,
        df: DataFrame,
        centroids: dict[str, StudyStructureCentroids],
        measurement_study_name: str,
        sample: str,
    ) -> None:
        coordinates = ['pixel x', 'pixel y']
        study_name = retrieve_primary_study(self.database_config_file, measurement_study_name)
        study_name = cast(str, study_name)
        location_data = DataFrame.from_dict(centroids[study_name][sample], orient='index')
        if location_data.shape[0] != df.shape[0]:
            present = location_data.shape[0]
            before = df.shape[0]
            message = f'Can not add location data {present} to feature matrix with {before} rows.'
            logger.error(message)
            logger.error(location_data)
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
