"""The core calculator for the UMAP dimensional reduction."""
import warnings
import pickle
import random

from io import BytesIO
from base64 import b64encode

import pandas as pd

from umap import UMAP  # type: ignore
from sklearn.impute import SimpleImputer  # type: ignore
from sklearn.pipeline import make_pipeline  # type: ignore
from sklearn.preprocessing import QuantileTransformer  # type: ignore
from matplotlib import pyplot as plt  # type: ignore
from matplotlib.colors import LinearSegmentedColormap  # type: ignore

from spatialprofilingtoolbox.workflow.component_interfaces.core import CoreJob
from spatialprofilingtoolbox.workflow.common.logging.performance_timer import PerformanceTimer
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.workflow.common.core import get_number_cells_to_be_processed
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

logger = colorized_logger(__name__)

UMAP_POINT_LIMIT = 50000


class ReductionVisualCoreJob(CoreJob):
    """Core/parallelizable functionality for the UMAP dimensional reduction workflow."""
    def __init__(
        self,
        study_name: str='',
        database_config_file: str='',
        performance_report_file: str='',
        results_file: str='',
        **kwargs  # pylint: disable=unused-argument
    ):
        self.study_name = study_name
        self.database_config_file = database_config_file
        self.performance_report_file = performance_report_file
        self.timer = PerformanceTimer()
        self.results_file = results_file

    def _calculate(self):
        self.log_job_info()
        self.generate_and_write_plots()
        self.wrap_up_timer()

    def generate_and_write_plots(self):
        plots_base64 = UMAPReducer.create_plots_base64(
            self.retrieve_feature_matrix_dense(cell_limit=UMAP_POINT_LIMIT)
        )
        self.write_to_table(plots_base64)

    def retrieve_feature_matrix_dense(self, cell_limit=None):
        sparse_df = self.retrieve_feature_matrix_sparse(cell_limit=cell_limit)
        return ReductionVisualCoreJob.sparse_to_dense(sparse_df)

    def retrieve_feature_matrix_sparse(self, cell_limit=None):
        if cell_limit is None:
            raise ValueError('Need to choose a cell_limit.')
        self.timer.record_timepoint(f'Start pulling data for the study: {self.study_name}')
        with DBCursor(database_config_file=self.database_config_file, study=self.study_name) as cursor:
            cursor.execute('''
            SELECT eq.histological_structure, cs.symbol, eq.quantity
            FROM expression_quantification eq
            JOIN chemical_species cs ON cs.identifier=eq.target
            JOIN histological_structure_identification hsi ON eq.histological_structure=hsi.histological_structure
            JOIN data_file df ON df.sha256_hash=hsi.data_source            
            JOIN specimen_data_measurement_process sdmp ON df.source_generation_process=sdmp.identifier
            JOIN specimen_collection_process scp ON scp.specimen=sdmp.specimen
            JOIN study_component sc ON scp.study=sc.component_study
            WHERE sc.primary_study=%s AND eq.histological_structure IN (
                    SELECT hsi2.histological_structure FROM histological_structure_identification hsi2
                    JOIN data_file df2 ON df2.sha256_hash=hsi2.data_source            
                    JOIN specimen_data_measurement_process sdmp2 ON df2.source_generation_process=sdmp2.identifier
                    JOIN specimen_collection_process scp2 ON scp2.specimen=sdmp2.specimen
                    JOIN study_component sc2 ON scp2.study=sc2.component_study
                    WHERE sc2.primary_study=%s
                    ORDER BY RANDOM() LIMIT %s
                )
            ;
            ''', (self.study_name, self.study_name, cell_limit))
            rows = cursor.fetchall()
        self.timer.record_timepoint('Finished pulling data.')
        sparse_df = pd.DataFrame(rows, columns=['structure', 'channel', 'quantity'])
        sparse_df = sparse_df.astype({'structure': str, 'channel': str, 'quantity': float})
        self.validate_all_structures_have_same_channels(sparse_df)
        logger.info('Dataframe pulled: %s', sparse_df.columns.values.tolist())
        return sparse_df

    @staticmethod
    def sparse_to_dense(sparse_df):
        logger.info('Converting sparse matrix to dense matrix.')
        dense_df = sparse_df.pivot(index='structure', columns=['channel'], values=['quantity'])
        logger.info('Dense matrix has size: %s', dense_df.shape)
        simplified_columns = [c[1] for c in dense_df.columns]
        dense_df.columns = simplified_columns
        return dense_df

    @staticmethod
    def select_randomly(series, number):
        if number > len(series):
            return series
        random.seed(101)
        return random.sample(series, k=number)

    def validate_all_structures_have_same_channels(self, df):
        if not (df.channel.value_counts() == len(df.structure.unique())).all():
            message = 'Cannot create a UMAP representation for study %s because given objects \
            have different sets of targets provided. Hence object representations have different \
            dimension which is incompatible with UMAP dimension reduction.'
            logger.error(message, self.study_name)
            raise ValueError(message % self.study_name)

    def write_to_table(self, plots_base64):
        if not self.probably_already_uploaded(plots_base64):
            self.upload_to_database(plots_base64)
        with open(self.results_file, 'wb') as file:
            pickle.dump([plots_base64, self.study_name], file)
        logger.info('Saved job output to file: %s', self.results_file)

    def probably_already_uploaded(self, plots_base64):
        with DBCursor(database_config_file=self.database_config_file, study=self.study_name) as cursor:
            cursor.execute('''
            SELECT COUNT(*) FROM umap_plots WHERE study=%s ;
            ''', (self.study_name,))
            count = cursor.fetchall()[0][0]
        if count == len(plots_base64):
            return True
        if count == 0:
            return False
        message = 'Mismatch between number %s of already-uploaded plots and %s \
                   available now to be uploaded.'
        raise ValueError(message, count, len(plots_base64))

    def upload_to_database(self, plots_base64):
        with DBCursor(database_config_file=self.database_config_file, study=self.study_name) as cursor:
            self.drop_existing_umap_plots(cursor)
            for channel, plot_base64 in plots_base64.items():
                cursor.execute('''
                INSERT INTO umap_plots (study, channel, png_base64)
                VALUES (%s, %s, %s) ;
                ''', (self.study_name, channel, plot_base64))
        logger.info('Saved %s plots to table umap_plots.', len(plots_base64))

    def drop_existing_umap_plots(self, cursor):
        cursor.execute('''
        DELETE FROM umap_plots WHERE study=%s ;
        ''', (self.study_name,))

    def log_job_info(self):
        number_cells = get_number_cells_to_be_processed(
            self.database_config_file,
            self.study_name,
        )
        logger.info('%s cells to be analyzed for study "%s".', number_cells, self.study_name)

    def wrap_up_timer(self):
        """Concludes low-level performance metric collection for this job."""
        df = self.timer.report(organize_by='fraction')
        logger.info('Report to: %s', self.get_performance_report_filename())
        df.to_csv(self.get_performance_report_filename(), index=False)

    def get_performance_report_filename(self):
        return self.performance_report_file


class UMAPReducer:
    """From dataframe create UMAP-reduced plots in base64 format."""
    @staticmethod
    def create_plots_base64(dense_df):
        normalized = UMAPReducer.preprocess_univariate_adjustments(dense_df)
        array = UMAPReducer.umap_reduce_to_2d(normalized)
        return UMAPReducer.make_plots_base64(array, dense_df)

    @staticmethod
    def preprocess_univariate_adjustments(df):
        pipeline = make_pipeline(SimpleImputer(strategy="mean"), QuantileTransformer())
        return pipeline.fit_transform(df.copy())

    @staticmethod
    def umap_reduce_to_2d(array):
        manifold = UMAP(random_state=99).fit(array)
        return manifold.transform(array)

    @staticmethod
    def get_cmap():
        return LinearSegmentedColormap.from_list('gg', ["lightgray", "lime"], N=256, gamma=1.0)

    @staticmethod
    def make_plots_base64(array, dense_df):
        """Make scatter plots with color-coded values

        :param array: 2D UMAP output in numpy format to use as plot coordinates.
        :param cell_matrix: Original channel intensity values, pandas DataFrame.
        """
        plots_base64 = {}
        cmap = UMAPReducer.get_cmap()
        for channel in dense_df.columns:
            _, axes = plt.subplots(figsize=(8, 8))
            axes.scatter(
                array[:, 0],
                array[:, 1],
                c=dense_df[channel],
                s=1,
                marker='.',
                cmap=cmap,
                alpha=0.9,
            )
            plt.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
            plt.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
            plt.tight_layout()
            plots_base64[channel] = UMAPReducer.retrieve_base64_from_plot()
            plt.close()
        return plots_base64

    @staticmethod
    def retrieve_base64_from_plot():
        inmemory_file = BytesIO()
        plt.savefig(inmemory_file, format='png', dpi=300)
        inmemory_file.seek(0)
        return b64encode(inmemory_file.getvalue()).decode('utf-8')
