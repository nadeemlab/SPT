"""
The core calculator for the proximity calculation on a single source file.
"""
# from itertools import combinations

import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree

from spatialprofilingtoolbox.db.feature_matrix_extractor import FeatureMatrixExtractor
from spatialprofilingtoolbox.workflow.common.logging.performance_timer import PerformanceTimer
from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.workflow.phenotype_proximity.computational_design import \
    PhenotypeProximityDesign
from spatialprofilingtoolbox.workflow.phenotype_proximity.job_generator import \
    ProximityJobGenerator
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class PhenotypeProximityCoreJob:
    """Core/parallelizable functionality for the phenotype proximity workflow."""
    computational_design: PhenotypeProximityDesign
    radius = 60

    def __init__(
        self,
        study_name: str='',
        database_config_file: str='',
        performance_report_filename: str='',
        job_index: str='',
        results_file: str='',
        **kwargs  # pylint: disable=unused-argument
    ):
        self.study_name = study_name
        self.database_config_file = database_config_file
        self.performance_report_filename = performance_report_filename
        self.timer = PerformanceTimer()
        self.results_file = results_file
        self.job_index = job_index
        self.sample_identifier = self.lookup_sample()
        self.phenotype_names = None
        self.tree = None

    def lookup_sample(self):
        generator = ProximityJobGenerator(self.study_name, self.database_config_file)
        return generator.retrieve_sample_identifiers()[int(self.job_index)]

    def get_performance_report_filename(self):
        return self.performance_report_filename

    def wrap_up_timer(self):
        """
        Concludes low-level performance metric collection for this job.
        """
        df = self.timer.report(organize_by='fraction')
        logger.info('Report to: %s', self.get_performance_report_filename())
        df.to_csv(self.get_performance_report_filename(), index=False)

    def get_number_cells_to_be_processed(self):
        with DatabaseConnectionMaker(self.database_config_file) as dcm:
            connection = dcm.get_connection()
            cursor = connection.cursor()
            cursor.execute('''
            SELECT COUNT(*)
            FROM
            histological_structure_identification hsi
            JOIN histological_structure hs ON hsi.histological_structure=hs.identifier
            JOIN data_file df ON df.sha256_hash=hsi.data_source
            JOIN specimen_data_measurement_process sdmp ON df.source_generation_process=sdmp.identifier
            JOIN specimen_collection_process scp ON scp.specimen=sdmp.specimen
            JOIN study_component sc ON sc.component_study=scp.study
            WHERE sc.primary_study=%s AND sdmp.specimen=%s AND hs.anatomical_entity='cell'
            ;
            ''', (self.study_name, self.sample_identifier))
            rows = cursor.fetchall()
            cursor.close()
        return rows[0][0]

    def log_job_info(self):
        number_cells = self.get_number_cells_to_be_processed()
        logger.info('%s cells to be analyzed for sample "%s".',number_cells,self.sample_identifier)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass

    def calculate(self):
        """
        The main calculation of this job, to be called by pipeline orchestration.
        """
        logger.info('Started core calculator job.')
        self.log_job_info()
        self._calculate()
        logger.info('Completed core calculator job.')
        self.wrap_up_timer()

    def _calculate(self):
        self.calculate_proximity()

    def calculate_proximity(self):
        self.timer.record_timepoint('Start pulling data for one sample.')
        bundle = FeatureMatrixExtractor.extract(database_config_file=self.database_config_file,
                                                specimen=self.sample_identifier)
        self.timer.record_timepoint('Finished pulling data for one sample.')
        study_name = list(bundle.keys())[0]
        _, sample = list(bundle[study_name]['feature matrices'].items())[0]
        cells = sample['dataframe']
        logger.info('Dataframe pulled: %s', cells.head())

        self.create_ball_tree(cells)

        channel_symbols_by_column_name = bundle[study_name]['channel symbols by column name']
        phenotype_identifiers, signatures = self.get_named_phenotype_signatures(
            channel_symbols_by_column_name)
        logger.info('Named phenotypes: ')
        logger.info(signatures)

        channels = sorted(channel_symbols_by_column_name.keys())
        singleton_signatures = [{'positive' : [column_name], 'negative' : []}
                                for column_name in channels]
        all_signatures = singleton_signatures + signatures

        cases = self.get_cases(all_signatures)
        proximity_metrics = [
            self.compute_proximity_metric_for_signature_pair(s1, s2, cells) for s1, s2 in cases]
        self.write_table(proximity_metrics, self.get_cases(channels + phenotype_identifiers))

    def create_ball_tree(self, cells):
        self.tree = BallTree(cells[['pixel x', 'pixel y']].to_numpy())

    def get_named_phenotype_signatures(self, context):
        with DatabaseConnectionMaker(self.database_config_file) as dcm:
            connection = dcm.get_connection()
            cursor = connection.cursor()
            cursor.execute('''
            SELECT cp.identifier, cp.symbol, cs.symbol, CASE cpc.polarity WHEN 'positive' THEN 1 WHEN 'negative' THEN 0 END coded_value
            FROM cell_phenotype cp
            JOIN cell_phenotype_criterion cpc ON cpc.cell_phenotype=cp.identifier
            JOIN chemical_species cs ON cs.identifier=cpc.marker
            JOIN study_component sc ON sc.component_study=cpc.study
            WHERE sc.primary_study=%s
            ORDER BY cp.identifier
            ;
            ''', (self.study_name,))
            rows = cursor.fetchall()
            cursor.close()
        lookup = {value : key for key, value in context.items()}
        criteria = pd.DataFrame(rows, columns=['phenotype', 'name', 'channel', 'polarity'])
        self.phenotype_names = {row['phenotype'] : row['name'] for _, row in criteria.iterrows()}
        criteria = criteria[['phenotype', 'channel', 'polarity']]

        def make_signature(df):
            return pd.Series({'signature' : {
                'positive' : [lookup[r['channel']] for _, r in df.iterrows() if r['polarity'] == 1],
                'negative' : [lookup[r['channel']] for _, r in df.iterrows() if r['polarity'] == 0],
            }})
        signatures = criteria.groupby(['phenotype']).apply(make_signature)
        by_identifier = {
            str(phenotype) : row['signature'] for phenotype, row in signatures.iterrows()}
        identifiers = sorted(by_identifier.keys())
        return identifiers, [by_identifier[i] for i in identifiers]

    def get_cases(self, items):
        return [(s1, s2) for s1 in items for s2 in items]

    def compute_proximity_metric_for_signature_pair(self, signature1, signature2, cells):
        logger.info('Doing case: %s, %s', signature1, signature2)
        value1, multiindex1 = self.get_value_and_multiindex(signature1)
        value2, multiindex2 = self.get_value_and_multiindex(signature1)

        logger.info(cells.head())

        logger.info('Value 1: %s', value1)
        logger.info('Multiindex 1: %s', multiindex1)
        logger.info('Index 1: %s', cells.set_index(multiindex1).index)

        logger.info('Value 2: %s', value2)
        logger.info('Multiindex 2: %s', multiindex2)
        logger.info('Index 2: %s', cells.set_index(multiindex2).index)

        mask1 = self.get_mask(cells, multiindex1, value1)
        mask2 = self.get_mask(cells, multiindex2, value2)

        logger.info('Mask 1: %s', mask2)
        logger.info('Mask 2: %s', mask2)

        source_cell_locations = cells.loc(axis=0)[mask1][['pixel x', 'pixel y']]
        within_radius_indices_list = self.tree.query_radius(
            source_cell_locations,
            PhenotypeProximityCoreJob.radius,
            return_distance=False,
        )

        logger.info('Queried indices: %s', within_radius_indices_list)
        counts = [
            sum(mask2[index] for index in list(indices))
            for indices in within_radius_indices_list
        ]
        logger.info('Counts: %s', counts)
        count = sum(counts) - sum(mask1 & mask2)
        source_count = sum(mask1)
        if source_count > 0:
            return count / source_count
        return None

    def get_mask(self, cells, multiindex, value):
        try:
            loc = cells.set_index(multiindex).index.get_loc(value)
        except KeyError:
            return (False,) * cells.shape[1]
        if isinstance(loc, slice):
            range1 = (False,)*(loc.start - 0)
            range2 = (True,)*(loc.stop - loc.start)
            range3 = (False,)*(cells.shape[1] - loc.stop)
            return range1 + range2 + range3
        if isinstance(loc, np.ndarray):
            return loc
        if isinstance(loc, int):
            return [i == loc for i in range(cells.shape[1])]
        raise ValueError(f'Could not select by index: {multiindex}. Got: {loc}')

    def get_value_and_multiindex(self, signature):
        value = (1,) * len(signature['positive']) + (0,) * len(signature['negative'])
        if len(value) == 1:
            value = value[0]
        multiindex = [*signature['positive'], *signature['negative']]
        return value, multiindex

    def write_table(self, proximity_metrics, cases):
        if len(proximity_metrics) != len(cases):
            raise ValueError('Number of computed features not equal to numbero cases.')
        df = pd.DataFrame(list(zip([case[0] for case in cases],
                                   [case[1] for case in cases],
                                   proximity_metrics)),
                          columns=['Phenotype 1', 'Phenotype 2', 'Proximity'])
        df.to_csv(self.results_file, sep='\t', index=False)
        logger.info('Computed metrics: %s', df.head())
