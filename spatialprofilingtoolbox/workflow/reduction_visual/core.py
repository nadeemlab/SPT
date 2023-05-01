"""
The core calculator for the UMAP dimensional reduction.
"""
import warnings
import pickle

from io import BytesIO
from base64 import b64encode

import pandas as pd
import numpy as np

from umap import UMAP
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import QuantileTransformer
from matplotlib import pyplot as plt
from  matplotlib.colors import LinearSegmentedColormap

from spatialprofilingtoolbox.workflow.component_interfaces.core import CoreJob
from spatialprofilingtoolbox.workflow.common.logging.performance_timer import PerformanceTimer
from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.workflow.reduction_visual.job_generator import \
    ReductionVisualJobGenerator
from spatialprofilingtoolbox.workflow.common.core import get_number_cells_to_be_processed
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

logger = colorized_logger(__name__)


class ReductionVisualCoreJob(CoreJob):
    """Core/parallelizable functionality for the UMAP dimensional reduction workflow."""
    def __init__(
        self,
        study_name: str='',
        database_config_file: str='',
        performance_report_file: str='',
        job_index: str='',
        results_file: str='',
        **kwargs  # pylint: disable=unused-argument
    ):
        self.study_name = study_name
        self.database_config_file = database_config_file
        self.performance_report_file = performance_report_file
        self.timer = PerformanceTimer()
        self.results_file = results_file
        self.job_index = job_index
        self.sample_identifier = self.lookup_sample()

    def lookup_sample(self):
        generator = ReductionVisualJobGenerator(self.study_name, self.database_config_file)
        return generator.retrieve_sample_identifiers()[int(self.job_index)]

    def _calculate(self):
        self.log_job_info()
        self.generate_and_write_plots()
        self.wrap_up_timer()

    def generate_and_write_plots(self):
        dense_df = self.retrieve_feature_matrix_dense()
        plot_strings = UMAPReducer.create_plots_base64(dense_df)
        self.write_to_table(plot_strings, dense_df)

    def retrieve_feature_matrix_dense(self):
        sparse_df = self.retrieve_feature_matrix_sparse()
        return ReductionVisualCoreJob.sparse_to_dense(sparse_df)

    def retrieve_feature_matrix_sparse(self):
        self.timer.record_timepoint(f'Start pulling data for the sample: {self.sample_identifier}')
        with DatabaseConnectionMaker(self.database_config_file) as dcm:
            connection = dcm.get_connection()
            cursor = connection.cursor()
            cursor.execute('''
            SELECT eq.histological_structure, cs.symbol, eq.quantity
            FROM expression_quantification eq
            JOIN chemical_species cs ON cs.identifier=eq.target
            JOIN histological_structure_identification hsi ON eq.histological_structure=hsi.histological_structure
            JOIN data_file df ON df.sha256_hash=hsi.data_source            
            JOIN specimen_data_measurement_process sdmp ON df.source_generation_process=sdmp.identifier
            WHERE sdmp.specimen=%s
            ;
            ''', (self.sample_identifier,))
            rows = cursor.fetchall()
            cursor.close()
        self.timer.record_timepoint('Finished pulling data.')
        sparse_df = pd.DataFrame(rows, columns=['structure', 'channel', 'quantity'])
        sparse_df = sparse_df.astype({'structure': str, 'channel': str, 'quantity': float})
        self.validate_all_structures_have_same_targets(sparse_df)
        logger.info('Dataframe pulled: %s', sparse_df.columns.values.tolist())
        return sparse_df

    @staticmethod
    def sparse_to_dense(sparse_df):
        logger.info('Converting sparse matrix to dense matrix.')
        dense_df = sparse_df.pivot(index='structure', columns=['channel'], values=['quantity'])
        logger.info('Feature matrix created, with columns: %s', dense_df.columns)
        return dense_df

    def validate_all_structures_have_same_targets(self, df):
        if not (df.target.value_counts() == len(df.structure.unique())).all():
            message = 'Cannot create a UMAP representation for study %s because given objects \
            have different sets of targets provided. Hence object representations have different \
            dimension which is incompatible with UMAP dimension reduction.'
            logger.error(message, self.study_name)
            raise ValueError(message % self.study_name)

    def write_to_table(self, plot_strings, dense_df):
        if len(plot_strings) != len(dense_df.columns):
            raise ValueError('Number of computed features not equal to number of cases.')
        df = pd.DataFrame(list(zip(cases, plot_strings)),
                          columns=['Target', 'PlotString'])

        bundle = [df, self.sample_identifier]
        with open(self.results_file, 'wb') as file:
            pickle.dump(bundle, file)
        logger.info('Computed metrics: %s', df.head())
        logger.info('Saved job output to file  %s', self.results_file)

    def log_job_info(self):
        number_cells = get_number_cells_to_be_processed(
            self.database_config_file,
            self.study_name,
            self.sample_identifier,
        )
        logger.info('%s cells to be analyzed for sample "%s".',number_cells,self.sample_identifier)

    def wrap_up_timer(self):
        """
        Concludes low-level performance metric collection for this job.
        """
        df = self.timer.report(organize_by='fraction')
        logger.info('Report to: %s', self.get_performance_report_filename())
        df.to_csv(self.get_performance_report_filename(), index=False)

    def get_performance_report_filename(self):
        return self.performance_report_file


class UMAPReducer:
    """
    From dataframe create UMAP-reduce plots in base64 format.
    """
    @staticmethod
    def create_plots_base64(dense_df):
        normalized = UMAPReducer.preprocess_univariate_adjustments(dense_df)
        array = UMAPReducer.umap_reduce_to_2d(normalized.to_numpy())
        return UMAPReducer.make_plots_base64(array, dense_df)

    @staticmethod
    def preprocess_univariate_adjustments(df):
        pipeline = make_pipeline(SimpleImputer(strategy="mean"), QuantileTransformer())
        return pipeline.fit_transform(df.copy())

    @staticmethod
    def umap_reduce_to_2d(array):
        manifold = UMAP().fit(array)
        return manifold.transform(array)

    @staticmethod
    def get_cmap():
        return LinearSegmentedColormap.from_list('gg', ["gray", "green"], N=256, gamma=1.0)

    @staticmethod
    def make_plots_base64(array, dense_df):
        """
        Make scatter plots with color-coded values

        :param array: 2D UMAP output in numpy format to use as plot coordinates.
        :param cell_matrix: Original channel intensity values, pandas DataFrame.
        """
        plots_base64 = {}
        cmap = UMAPReducer.get_cmap()
        for channel in dense_df.columns:
            figure, axes = plt.subplots(figsize=(6, 5))
            points = axes.scatter(
                array[:, 0],
                array[:, 1],
                c=dense_df[channel],
                s=5,
                cmap=cmap,
                alpha=0.7,
            )
            figure.colorbar(points)
            plot_svg_base64 = UMAPReducer.retrieve_base64_from_plot()
            plots_base64[channel] = plot_svg_base64
            plt.close()
        return plots_base64

    @staticmethod
    def retrieve_base64_from_plot():
        inmemory_file = BytesIO()
        plt.savefig(inmemory_file, format='svg')
        inmemory_file.seek(0)
        return b64encode(inmemory_file.getvalue())
