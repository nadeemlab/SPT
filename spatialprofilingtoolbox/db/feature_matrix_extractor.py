"""
Convenience provision of a feature matrix for each study, the data retrieved from the SPT database.
"""

from enum import Enum
from enum import auto
from typing import cast

from pandas import DataFrame
from psycopg2.extensions import cursor as Psycopg2Cursor

from spatialprofilingtoolbox import DatabaseConnectionMaker
from spatialprofilingtoolbox.db.stratification_puller import StratificationPuller
from spatialprofilingtoolbox.workflow.common.structure_centroids_puller import \
    StructureCentroidsPuller
from spatialprofilingtoolbox.workflow.common.sparse_matrix_puller import SparseMatrixPuller
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)

BundlePart = dict[str, DataFrame | str | dict[str, DataFrame | str ]]
Bundle = dict[str, dict[str, BundlePart]]

class DBSource(Enum):
    """Indicator of intended database source."""
    CURSOR = auto()
    CONFIG_FILE = auto()
    UNKNOWN = auto()


class FeatureMatrixExtractor:
    """Pull from the database and create convenience bundle of feature matrices and metadata."""
    cursor: Psycopg2Cursor
    database_config_file: str | None
    db_source: DBSource

    def __init__(self,
        cursor: Psycopg2Cursor | None=None,
        database_config_file: str | None=None,
    ):
        self.cursor = cast(Psycopg2Cursor, cursor)
        self.database_config_file = database_config_file
        if cursor is not None:
            self.db_source = DBSource.CURSOR
        elif database_config_file is not None:
            self.db_source = DBSource.CONFIG_FILE
        else:
            self.db_source = DBSource.UNKNOWN
        self._report_on_arguments()

    def _report_on_arguments(self):
        if self.cursor is None and self.database_config_file is None:
            logger.error('Must supply either cursor or database_config_file.')
        if self.cursor is not None and self.database_config_file is not None:
            message = 'A cursor and database configuration file were both specified. Using the '\
                'cursor.'
            logger.warning(message)

    def extract(self,
        specimen: str | None=None,
        study: str | None=None,
        continuous_also: bool=False,
    ) -> Bundle | None:
        extraction = None
        match self.db_source:
            case DBSource.CURSOR:
                extraction = self._extract(
                    specimen=specimen,
                    study=study,
                    continuous_also=continuous_also,
                )
            case DBSource.CONFIG_FILE:
                with DatabaseConnectionMaker(self.database_config_file) as dcm:
                    with dcm.get_connection().cursor() as cursor:
                        self.cursor = cursor
                        extraction = self._extract(
                            specimen=specimen,
                            study=study,
                            continuous_also=continuous_also,
                        )
            case DBSource.UNKNOWN:
                logger.error('The database source can not be determined.')
        return extraction

    def _extract(self,
        specimen: str | None=None,
        study: str | None=None,
        continuous_also: bool=False,
    ) -> Bundle | None:
        data_arrays = self._retrieve_expressions_from_database(
            specimen=specimen,
            study=study,
            continuous_also=continuous_also,
        )
        centroid_coordinates = self._retrieve_structure_centroids_from_database(
            specimen=specimen,
            study=study,
        )
        stratification = self._retrieve_derivative_stratification_from_database()
        study_component_lookup = self._retrieve_study_component_lookup()
        merged = self._merge_dictionaries(
            self._create_feature_matrices(data_arrays, centroid_coordinates),
            self._create_channel_information(data_arrays),
            stratification,
            new_keys=['feature matrices','channel symbols by column name', 'sample cohorts'],
            study_component_lookup=study_component_lookup,
        )
        if merged is None:
            return None
        if study is not None:
            for key in list(merged.keys()):
                if not key == study:
                    del merged[key]
        return merged

    @staticmethod
    def redact_dataframes(extraction):
        for study_name, study in extraction.items():
            for specimen in study['feature matrices'].keys():
                extraction[study_name]['feature matrices'][specimen]['dataframe'] = None
                key = 'continuous dataframe'
                if key in extraction[study_name]['feature matrices'][specimen]:
                    extraction[study_name]['feature matrices'][specimen][key] = None
            extraction[study_name]['sample cohorts']['assignments'] = None
            extraction[study_name]['sample cohorts']['strata'] = None

    def _retrieve_expressions_from_database(self,
        specimen: str | None=None,
        study: str | None=None,
        continuous_also: bool=False,
    ):
        logger.info('Retrieving expression data from database.')
        puller = SparseMatrixPuller(self.cursor)
        puller.pull(specimen=specimen, study=study, continuous_also=continuous_also)
        data_arrays = puller.get_data_arrays()
        logger.info('Done retrieving expression data from database.')
        return data_arrays.get_studies()

    def _retrieve_structure_centroids_from_database(self,
        specimen: str | None=None,
        study: str | None=None,
    ):
        logger.info('Retrieving polygon centroids from shapefiles in database.')
        puller = StructureCentroidsPuller(self.cursor)
        puller.pull(specimen=specimen, study=study)
        structure_centroids = puller.get_structure_centroids()
        logger.info('Done retrieving centroids.')
        return structure_centroids.get_studies()

    def _retrieve_derivative_stratification_from_database(self):
        logger.info('Retrieving stratification from database.')
        puller = StratificationPuller(self.cursor)
        puller.pull()
        stratification = puller.get_stratification()
        logger.info('Done retrieving stratification.')
        return stratification

    def _retrieve_study_component_lookup(self):
        self.cursor.execute('SELECT * FROM study_component ; ')
        rows = self.cursor.fetchall()
        lookup = {}
        for row in rows:
            lookup[row[1]] = row[0]
        return lookup

    def _create_feature_matrices(self, data_arrays, centroid_coordinates):
        logger.info('Creating feature matrices from binary data arrays and centroids.')
        matrices = {}
        for k, study_name in enumerate(sorted(list(data_arrays.keys()))):
            study = data_arrays[study_name]
            matrices[study_name] = {}
            for j, specimen in enumerate(sorted(list(study['data arrays by specimen'].keys()))):
                logger.debug('Specimen %s .', specimen)
                expressions = study['data arrays by specimen'][specimen]
                number_channels = len(study['target index lookup'])
                rows = [
                    self._create_feature_matrix_row(
                        centroid_coordinates[study_name][specimen][i],
                        expressions[i],
                        number_channels,
                    )
                    for i in range(len(expressions))
                ]
                dataframe = DataFrame(
                    rows,
                    columns=['pixel x', 'pixel y'] + [f'F{i}' for i in range(number_channels)],
                )
                matrices[study_name][specimen] = {
                    'dataframe': dataframe,
                    'filename': f'{k}.{j}.tsv',
                }

            if 'continuous data arrays by specimen' in study:
                specimens = list(study['continuous data arrays by specimen'].keys())
                for j, specimen in enumerate(sorted(specimens)):
                    logger.debug('Specimen %s .', specimen)
                    expression_vectors = study['continuous data arrays by specimen'][specimen]
                    number_channels = len(study['target index lookup'])
                    dataframe = DataFrame(
                        expression_vectors,
                        columns=[f'F{i}' for i in range(number_channels)],
                    )
                    matrices[study_name][specimen]['continuous dataframe'] = dataframe

        logger.info('Done creating feature matrices.')
        return matrices

    @staticmethod
    def _create_feature_matrix_row(centroid, binary, number_channels):
        template = '{0:0%sb}' % number_channels   # pylint: disable=consider-using-f-string
        feature_vector = [int(value) for value in list(template.format(binary)[::-1])]
        return [centroid[0], centroid[1]] + feature_vector

    def _create_channel_information(self, data_arrays):
        return {
            study_name: self._create_channel_information_for_study(study)
            for study_name, study in data_arrays.items()
        }

    def _create_channel_information_for_study(self, study):
        logger.info('Aggregating channel information for one study.')
        targets = {
            int(index): target
            for target, index in study['target index lookup'].items()
        }
        symbols = {
            target: symbol
            for symbol, target in study['target by symbol'].items()
        }
        logger.info('Done aggregating channel information.')
        return {
            f'F{i}': symbols[targets[i]]
            for i in sorted([int(index) for index in targets.keys()])
        }

    def _merge_dictionaries(self,
        *args,
        new_keys: list,
        study_component_lookup: dict
    ) -> Bundle | None:
        if not len(args) == len(new_keys):
            logger.error(
                "Can not match up dictionaries to be merged with the list of key names to be "
                "issued for them."
            )
            return None

        merged: dict = {}
        for i in range(len(new_keys)):
            for substudy, value in args[i].items():
                merged[study_component_lookup[substudy]] = {}

        for i, key in enumerate(new_keys):
            for substudy, value in args[i].items():
                merged[study_component_lookup[substudy]][key] = value

        logger.info('Done merging into a single dictionary bundle.')
        return merged
