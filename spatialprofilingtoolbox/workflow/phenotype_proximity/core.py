"""The core calculator for the proximity calculation on a single source file."""

import warnings
import pickle


import pandas as pd
from pandas import DataFrame
from sklearn.neighbors import BallTree  # type: ignore

from spatialprofilingtoolbox.workflow.component_interfaces.core import CoreJob
from spatialprofilingtoolbox.db.feature_matrix_extractor import FeatureMatrixExtractor
from spatialprofilingtoolbox.workflow.common.logging.performance_timer import \
    PerformanceTimerReporter
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.workflow.phenotype_proximity.job_generator import \
    ProximityJobGenerator
from spatialprofilingtoolbox.workflow.common.core import get_number_cells_to_be_processed
from spatialprofilingtoolbox.workflow.common.proximity import \
    compute_proximity_metric_for_signature_pair
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

logger = colorized_logger(__name__)

ProximityComputed = dict[tuple[str, str, float], float | None]

class PhenotypeProximityCoreJob(CoreJob):
    """Core/parallelizable functionality for the phenotype proximity workflow."""
    radii = [60, 120]
    tree: BallTree

    def __init__(self,
        study_name: str = '',
        database_config_file: str = '',
        performance_report_file: str = '',
        results_file: str = '',
        **kwargs  # pylint: disable=unused-argument
    ) -> None:
        self.study_name = study_name
        self.database_config_file = database_config_file
        self.results_file = results_file
        self.sample_identifier = self.lookup_sample(kwargs['job_index'])
        self.reporter = PerformanceTimerReporter(performance_report_file, logger)

    def lookup_sample(self, job_index):
        generator = ProximityJobGenerator(self.study_name, self.database_config_file)
        return generator.retrieve_sample_identifiers()[int(job_index)]

    def _calculate(self):
        self.log_job_info()
        self.calculate_proximity()
        self.reporter.wrap_up_timer()

    def log_job_info(self):
        number_cells = get_number_cells_to_be_processed(
            self.database_config_file,
            self.study_name,
            self.sample_identifier,
        )
        logger.info('%s cells to be analyzed in sample "%s".', number_cells, self.sample_identifier)

    def calculate_proximity(self):
        self.reporter.record_timepoint('Start pulling data for one sample.')
        bundle = FeatureMatrixExtractor(database_config_file=self.database_config_file).extract(
            specimen=self.sample_identifier)
        self.reporter.record_timepoint('Finished pulling data for one sample.')
        identifier = list(bundle.keys())[0]
        cells = bundle[identifier].dataframe
        logger.info('Dataframe pulled: %s', cells.head())

        self.create_ball_tree(cells)

        # Assemble phenotype signatures for every channel and phenotype
        channels = sorted(
            [col_name[2:] for col_name in cells.columns if col_name.startswith('C ')]
        )
        phenotypes = sorted(
            [col_name[2:] for col_name in cells.columns if col_name.startswith('P ')]
        )
        signatures = self.get_named_phenotype_signatures()
        assert set(phenotypes) == signatures.keys()
        logger.info('Named phenotypes:')
        logger.info(phenotypes)
        all_features = channels + phenotypes
        signatures.update({
            column_name: PhenotypeCriteria(
                positive_markers=[column_name],
                negative_markers=[],
            ) for column_name in channels
        })

        # Calculate proximity metrics for every phenotype pair and write
        proximity_metrics = {
            (f1, f2, r): compute_proximity_metric_for_signature_pair(
                signatures[f1],
                signatures[f2],
                r,
                cells,
                self.tree,
            ) for f1, f2, r in self.get_cases(all_features)
        }
        self.write_table(proximity_metrics)

    def create_ball_tree(self, cells):
        self.tree = BallTree(cells[['pixel x', 'pixel y']].to_numpy())

    def get_named_phenotype_signatures(self) -> dict[str, PhenotypeCriteria]:
        kwargs = {'database_config_file': self.database_config_file, 'study': self.study_name}
        with DBCursor(**kwargs) as cursor:
            cursor.execute('''
            SELECT
                cp.symbol,
                cs.symbol,
                CASE cpc.polarity WHEN 'positive' THEN 1 WHEN 'negative' THEN 0 END coded_value
            FROM cell_phenotype cp
            JOIN cell_phenotype_criterion cpc ON cpc.cell_phenotype=cp.identifier
            JOIN chemical_species cs ON cs.identifier=cpc.marker
            JOIN study_component sc ON sc.component_study=cpc.study
            WHERE sc.primary_study=%s
            ORDER BY cp.identifier
            ;
            ''', (self.study_name,))
            rows = cursor.fetchall()
        criteria = DataFrame(rows, columns=['phenotype', 'channel', 'polarity'])

        def list_channels(df: DataFrame, polarity: int) -> list[str]:
            return [r['channel'] for _, r in df.iterrows() if r['polarity'] == polarity]

        def make_signature(df) -> PhenotypeCriteria:
            return PhenotypeCriteria(
                positive_markers=list_channels(df, 1),
                negative_markers=list_channels(df, 0),
            )
        by_identifier: dict[str, PhenotypeCriteria] = {}
        for phenotype, criteria in criteria.groupby('phenotype'):
            by_identifier[str(phenotype)] = make_signature(criteria)
        return by_identifier

    def get_cases(self, items: list[str]) -> list[tuple[str, str, float]]:
        return [
            (f1, f2, radius)
            for f1 in items
            for f2 in items
            for radius in PhenotypeProximityCoreJob.radii
        ]

    def write_table(self, proximity_metrics: ProximityComputed) -> None:
        rows = [(f1, f2, r, m) for (f1, f2, r), m in proximity_metrics.items()]
        columns = ['Phenotype 1', 'Phenotype 2', 'Pixel radius', 'Proximity']
        df = DataFrame(rows, columns=columns)
        bundle = [df, self.sample_identifier]
        with open(self.results_file, 'wb') as file:
            pickle.dump(bundle, file)
        logger.info('Computed metrics: %s', df.head())
