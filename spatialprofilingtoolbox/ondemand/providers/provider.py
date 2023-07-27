"""Base class for providers."""

from abc import ABC
from sys import exit
from re import search
from os import listdir
from os.path import join, isfile
from json import loads

from pandas import DataFrame

from spatialprofilingtoolbox.workflow.common.structure_centroids import StructureCentroids
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class Provider(ABC):
    """Base class for Provider instances, since they share data ingestion methods."""

    def __init__(self, data_directory: str, load_centroids: bool = False) -> None:
        """Load from a precomputed JSON artifact in the data directory."""
        self.load_expressions_indices(data_directory)

        if load_centroids:
            loader = StructureCentroids()
            loader.load_from_file(data_directory)
            self.centroids = loader.get_studies()
        else:
            self.centroids = None

        self.load_data_matrices(data_directory, self.centroids)
        logger.info('%s is finished loading source data.', type(self).__name__)

    def load_expressions_indices(self, data_directory: str) -> None:
        """Load expression indices from a precomputed JSON artifact."""
        logger.debug('Searching for source data in: %s', data_directory)
        json_files = [f for f in listdir(data_directory) if isfile(
            join(data_directory, f)) and search(r'\.json$', f)]
        if len(json_files) != 1:
            logger.error('Did not find index JSON file.')
            exit(1)
        with open(join(data_directory, json_files[0]), 'rt', encoding='utf-8') as file:
            root = loads(file.read())
            entries = root[list(root.keys())[0]]
            self.studies = {}
            for entry in entries:
                self.studies[entry['specimen measurement study name']] = entry

    def load_data_matrices(self, data_directory: str, centroids: dict | None = None) -> None:
        """Load data matrices from a precomputed JSON artifact."""
        self.data_arrays: dict[str, dict[str, DataFrame]] = {}
        for study_name in self.get_study_names():
            if centroids is None:
                self.data_arrays[study_name] = {
                    item['specimen']: self.get_data_array_from_file(
                        join(data_directory, item['filename'])
                    )
                    for item in self.studies[study_name]['expressions files']
                }
            else:
                self.data_arrays[study_name] = {
                    item['specimen']: self.get_data_array_from_file(
                        join(data_directory, item['filename']),
                        self.studies[study_name]['target index lookup'],
                        self.studies[study_name]['target by symbol'],
                        study_name,
                        item['specimen'],
                        centroids,
                    )
                    for item in self.studies[study_name]['expressions files']
                }
                shapes = [
                    df.shape for df in self.data_arrays[study_name].values()]
                logger.debug('Loaded dataframes of sizes %s', shapes)
                number_specimens = len(self.data_arrays[study_name])
                specimens = self.data_arrays[study_name].keys()
                logger.debug('%s specimens loaded (%s).',
                             number_specimens, specimens)

    def get_study_names(self) -> list[str]:
        """Retrieve names of the studies held in memory."""
        return self.studies.keys()

    # def get_data_array_from_file(self, filename: str) -> list[int]:
    #     """Load data arrays from a precomputed JSON artifact."""
    #     data_array = []
    #     with open(filename, 'rb') as file:
    #         buffer = None
    #         while buffer != b'':
    #             buffer = file.read(8)
    #             data_array.append(int.from_bytes(buffer, 'little'))
    #     return data_array

    def get_data_array_from_file(
        self,
        filename: str,
        target_index_lookup: dict | None = None,
        target_by_symbol: dict | None = None,
        study_name: str | None = None,
        sample: str | None = None,
        centroids: dict | None = None,
    ) -> DataFrame:
        """Load data arrays from a precomputed JSON artifact."""
        rows = []
        columns = self.list_columns(target_index_lookup, target_by_symbol) if \
            (target_index_lookup is not None) and (target_by_symbol is not None) else ['entry']
        with open(filename, 'rb') as file:
            buffer = None
            while True:
                buffer = file.read(8)
                if buffer == b'':
                    break
                if target_index_lookup is None:
                    buffer = file.read(8)
                    row = [int.from_bytes(buffer, 'little')]
                else:
                    binary_expression_64_string = ''.join([
                        ''.join(list(reversed(bin(ii)[2:].rjust(8, '0'))))
                        for ii in buffer
                    ])
                    truncated_to_channels = binary_expression_64_string[0:len(
                        columns)]
                    row = [int(b) for b in list(truncated_to_channels)]
                    rows.append(row)
        df = DataFrame(rows, columns=columns)
        if (centroids is not None) and (study_name is not None) and (sample is not None):
            df['pixel x'] = [point[0]
                             for point in centroids[study_name][sample]]
            df['pixel y'] = [point[1]
                             for point in centroids[study_name][sample]]
        return df

    @staticmethod
    def list_columns(target_index_lookup: dict, target_by_symbol: dict) -> list[str]:
        target_by_index = {value: key for key,
                           value in target_index_lookup.items()}
        symbol_by_target = {value: key for key,
                            value in target_by_symbol.items()}
        return [
            symbol_by_target[target_by_index[i]]
            for i in range(len(target_by_index))
        ]
