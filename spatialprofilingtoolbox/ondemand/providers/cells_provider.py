"""Provide bundle of position and phenotype information at the cell-level granularity."""

from json import dumps

from spatialprofilingtoolbox.db.simple_method_cache import simple_instance_method_cache
from spatialprofilingtoolbox.ondemand.providers.provider import OnDemandProvider
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CellsProvider(OnDemandProvider):
    """Provide bundle of position and phenotype information at the cell-level granularity."""

    def __init__(self, timeout: int, database_config_file: str | None) -> None:
        logger.info('Start loading location data and phenotype data for cells provider.')
        super().__init__(timeout, database_config_file, load_centroids=True)
        self._dropna_in_data_arrays()
        logger.info('Done loading for cells provider.')

    @classmethod
    def service_specifier(cls) -> str:
        return 'cells'

    def _dropna_in_data_arrays(self) -> None:
        for _, _data_arrays in self.data_arrays.items():
            for sample_identifier, df in _data_arrays.items():
                former = df.shape
                df.dropna(inplace=True)
                current = df.shape
                if current[0] != former[0]:
                    defect0 = former[0] - current[0]
                    message = f'Dropped {defect0} rows due to to NAs, for {sample_identifier}.'
                    logger.info(message)
                if current[1] != former[1]:
                    defect1 = former[1] - current[1]
                    message = f'Dropped {defect1} columns due to to NAs, for {sample_identifier}.'
                    logger.warning(message)

    @simple_instance_method_cache(maxsize=10000, log=True)
    def get_bundle(self, measurement_study: str, sample: str) -> str:
        """
        JSON-formatted representation of the cell-level data for the given sample.
        The format is:
        {
            'feature_names': ['histological structure id', 'pixel x', 'pixel y', '<feature name1>', ...],
            'cells': [
                [<histological structure id integer>, <pixel x>, <pixel y>, <feature value 0/1>, ...],
                ...
            ]
        }
        """
        df = self.data_arrays[measurement_study][sample].drop('integer', axis=1).reset_index()
        additional = ['histological_structure_id', 'pixel x', 'pixel y']
        feature_names = sorted(list(set(list(df.columns)).difference(set(additional))))
        feature_names = ['histological_structure_id', 'pixel x', 'pixel y'] + feature_names
        values = df[feature_names].to_json(orient='values')
        return f'''{{
            "feature_names": {dumps(feature_names)},
            "cells": {values}
        }}
        '''
