"""Convenience provision of a feature matrix for each study, retrieved from the SPT database."""

from enum import Enum
from enum import auto
from typing import cast, Any

from pandas import DataFrame
from psycopg2.extensions import cursor as Psycopg2Cursor

from spatialprofilingtoolbox import DatabaseConnectionMaker
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.db.phenotypes import PhenotypesAccess
from spatialprofilingtoolbox.db.stratification_puller import StratificationPuller
from spatialprofilingtoolbox.db.study_access import StudyAccess
from spatialprofilingtoolbox.workflow.common.structure_centroids_puller import \
    StructureCentroidsPuller
from spatialprofilingtoolbox.workflow.common.sparse_matrix_puller import SparseMatrixPuller
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)

StudyBundle = dict[str, dict[str, Any]]


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
        cursor: Psycopg2Cursor | None = None,
        database_config_file: str | None = None,
    ) -> None:
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
        specimen: str | None = None,
        study: str | None = None,
        continuous_also: bool = False,
    ) -> StudyBundle:
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
        specimen: str | None = None,
        study: str | None = None,
        continuous_also: bool = False,
    ) -> StudyBundle:
        if (specimen is None) == (study is None):
            raise ValueError('Must specify exactly one of specimen or study.')
        data_arrays = self._retrieve_expressions_from_database(
            specimen=specimen,
            study=study,
            continuous_also=continuous_also,
        )
        centroid_coordinates = self._retrieve_structure_centroids_from_database(
            specimen=specimen,
            study=study,
        )
        if study is None:
            assert specimen is not None
            study = StudyAccess(self.cursor).get_study_from_specimen(specimen)
        stratification = self._retrieve_derivative_stratification_from_database()
        for substudy in self._retrieve_component_studies(study):
            if substudy in stratification:
                break
        else:
            raise RuntimeError('Stratification substudy not found for study.')

        channel_information = self._create_channel_information(data_arrays)
        phenotypes, phenotype_information = self._retrieve_phenotypes(study, channel_information)
        return {
            'feature matrices': self._create_feature_matrices(
                data_arrays,
                centroid_coordinates,
                phenotypes
            ),
            'channel symbols by column name': channel_information,
            'sample cohorts': stratification[substudy],
            'phenotype symbols by column name': phenotype_information
        }

    @staticmethod
    def redact_dataframes(study: dict[str, dict[str, Any]]) -> None:
        for specimen in study['feature matrices'].keys():
            study['feature matrices'][specimen]['dataframe'] = None
            key = 'continuous dataframe'
            if key in study['feature matrices'][specimen]:
                study['feature matrices'][specimen][key] = None
        study['sample cohorts']['assignments'] = None
        study['sample cohorts']['strata'] = None

    def _retrieve_expressions_from_database(self,
        specimen: str | None = None,
        study: str | None = None,
        continuous_also: bool = False,
    ) -> dict[str, dict[str, Any]]:
        logger.info('Retrieving expression data from database.')
        puller = SparseMatrixPuller(self.cursor)
        puller.pull(specimen=specimen, study=study, continuous_also=continuous_also)
        data_arrays = puller.get_data_arrays()
        logger.info('Done retrieving expression data from database.')
        return list(data_arrays.get_studies().values())[0]

    def _retrieve_structure_centroids_from_database(self,
        specimen: str | None = None,
        study: str | None = None,
    ) -> dict[str, Any]:
        logger.info('Retrieving polygon centroids from shapefiles in database.')
        puller = StructureCentroidsPuller(self.cursor)
        puller.pull(specimen=specimen, study=study)
        structure_centroids = puller.get_structure_centroids()
        logger.info('Done retrieving centroids.')
        return list(structure_centroids.get_studies().values())[0]

    def _retrieve_phenotypes(self,
        study_name: str,
        channel_names: dict[str, str]
    ) -> tuple[dict[str, PhenotypeCriteria], dict[str, str]]:
        logger.info('Retrieving phenotypes from database.')
        channel_to_column_name = {n: c for c, n in channel_names.items()}
        phenotypes: dict[str, PhenotypeCriteria] = {}
        phenotype_access = PhenotypesAccess(self.cursor)
        phenotype_information: dict[str, str] = {}
        for i, symbol_data in enumerate(phenotype_access.get_phenotype_symbols(study_name)):
            column_name = f'P{i}'
            symbol = symbol_data.handle_string
            phenotypes[column_name] = phenotype_access.get_phenotype_criteria(study_name, symbol)
            phenotype_information[column_name] = symbol

            # Convert marker lists to FeatureMatrixExtractor column names.
            phenotypes[column_name].positive_markers = [
                channel_to_column_name[marker]
                for marker in phenotypes[column_name].positive_markers
            ]
            phenotypes[column_name].negative_markers = [
                channel_to_column_name[marker]
                for marker in phenotypes[column_name].negative_markers
            ]
        logger.info('Done retrieving phenotypes.')
        return phenotypes, phenotype_information

    def _retrieve_derivative_stratification_from_database(self) -> dict[str, dict[str, Any]]:
        logger.info('Retrieving stratification from database.')
        puller = StratificationPuller(self.cursor)
        puller.pull()
        stratification = puller.get_stratification()
        logger.info('Done retrieving stratification.')
        return stratification

    def _retrieve_component_studies(self, study: str) -> set[str]:
        self.cursor.execute(f'''
            SELECT component_study
            FROM study_component
            WHERE primary_study = '{study}';
        ''')
        rows = self.cursor.fetchall()
        lookup: set[str] = set()
        for row in rows:
            lookup.add(row[0])
        return lookup

    def _create_feature_matrices(self,
        study: dict[str, dict[str, Any]],
        centroid_coordinates: dict[str, Any],
        phenotypes: dict[str, PhenotypeCriteria],
    ) -> dict[str, DataFrame]:
        logger.info('Creating feature matrices from binary data arrays and centroids.')
        matrices = {}
        for j, specimen in enumerate(sorted(list(study['data arrays by specimen'].keys()))):
            logger.debug('Specimen %s .', specimen)
            expressions = study['data arrays by specimen'][specimen]
            number_channels = len(study['target index lookup'])
            rows = [
                self._create_feature_matrix_row(
                    centroid_coordinates[specimen][i],
                    expressions[i],
                    number_channels,
                ) for i in range(len(expressions))
            ]
            dataframe = DataFrame(
                rows,
                columns=['pixel x', 'pixel y'] + [f'F{i}' for i in range(number_channels)],
            )
            for column_name, criteria in phenotypes.items():
                dataframe[column_name] = (
                    dataframe[criteria.positive_markers].all(axis=1) &
                    dataframe[criteria.negative_markers].all(axis=1)
                ).astype(int)
            matrices[specimen] = {
                'dataframe': dataframe,
                'filename': f'{j}.tsv',
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
                matrices[specimen]['continuous dataframe'] = dataframe

        logger.info('Done creating feature matrices.')
        return matrices

    @staticmethod
    def _create_feature_matrix_row(
        centroid: tuple[float, float],
        binary: list[str],
        number_channels: int,
    ) -> list[float | int]:
        template = '{0:0%sb}' % number_channels   # pylint: disable=consider-using-f-string
        feature_vector: list[int] = [int(value) for value in list(template.format(binary)[::-1])]
        return [centroid[0], centroid[1]] + feature_vector

    def _create_channel_information(self,
        study_information: dict[str, dict[str, Any]]
    ) -> dict[str, str]:
        logger.info('Aggregating channel information for one study.')
        targets = {
            int(index): target
            for target, index in study_information['target index lookup'].items()
        }
        symbols = {
            target: symbol
            for symbol, target in study_information['target by symbol'].items()
        }
        logger.info('Done aggregating channel information.')
        return {
            f'F{i}': symbols[targets[i]]
            for i in sorted([int(index) for index in targets.keys()])
        }
