"""
The core calculator for the proximity calculation on a single source file.
"""
import warnings
import pickle

from io import BytesIO
import base64

import pandas as pd
import numpy as np

import umap  # pip install umap-learn
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import QuantileTransformer
from matplotlib import pyplot as plt
from  matplotlib.colors import LinearSegmentedColormap

from spatialprofilingtoolbox.workflow.component_interfaces.core import CoreJob
from spatialprofilingtoolbox.db.feature_matrix_extractor import FeatureMatrixExtractor
from spatialprofilingtoolbox.workflow.common.logging.performance_timer import PerformanceTimer
from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.workflow.phenotype_proximity.job_generator import \
    ProximityJobGenerator
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

logger = colorized_logger(__name__)


class ReductionVisualCoreJob(CoreJob):
    """Core/parallelizable functionality for the phenotype proximity workflow."""
    radii = [60, 120]

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
        self.target_order = None
        self.cmap = LinearSegmentedColormap.from_list('gg',["gray", "green"], N=256, gamma=1.0)

    def lookup_sample(self):
        generator = ProximityJobGenerator(self.study_name, self.database_config_file)
        return generator.retrieve_sample_identifiers()[int(self.job_index)]

    def get_performance_report_filename(self):
        return self.performance_report_file

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
            # todo: select rows for the specific study
            cursor.execute('''
            SELECT COUNT(*) FROM expression_quantification
            ;
            ''')
            rows = cursor.fetchall()
            cursor.close()
        return rows[0][0]

    def _calculate(self):
        self.log_job_info()
        self.generate_plots()
        self.wrap_up_timer()

    def log_job_info(self):
        number_cells = self.get_number_cells_to_be_processed()
        logger.info('%s cells to be analyzed for sample "%s".',number_cells,self.sample_identifier)

    def generate_plots(self):
        self.timer.record_timepoint('Start pulling data for the study.')
        with DatabaseConnectionMaker(self.database_config_file) as dcm:
            connection = dcm.get_connection()
            cursor = connection.cursor()
            cursor.execute(f'''
            SELECT eq.histological_structure, target, quantity
            FROM expression_quantification eq
            JOIN histological_structure_identification hsi ON eq.histological_structure=hsi.histological_structure
            JOIN data_file df ON df.sha256_hash=hsi.data_source            
            JOIN specimen_data_measurement_process sdmp ON df.source_generation_process=sdmp.identifier
            JOIN specimen_collection_process scp ON scp.specimen=sdmp.specimen
            JOIN study_component sc ON scp.study=sc.component_study
            WHERE sc.primary_study='{self.study_name}'
            ;
            ''')
            rows = cursor.fetchall()
            cursor.close()

        self.timer.record_timepoint('Finished pulling data for the study.')

        quantity_df = pd.DataFrame(rows, columns=['structure', 'target', 'quantity'])
        quantity_df = quantity_df.astype(
            {'structure': 'int64', 'target': 'int64', 'quantity': 'float'})

        # check that all structures (cells) have the same set of targets
        if not (quantity_df.target.value_counts() == len(quantity_df.structure.unique())).all():
            # logger.warn("Cannot create a UMAP representation for study {study_id} because given objects have different sets of targets provided. Hence object representations have different dimension which is incompatible with UMAP dimension reduction.")
            print(
                "Cannot create a UMAP representation for study {study_id} because given objects have different sets of targets provided. Hence object representations have different dimension which is incompatible with UMAP dimension reduction.")

        # take target order from the first structure
        self.target_order = quantity_df.loc[quantity_df.structure == quantity_df.structure.iloc[0], 'target'].values

        quantity_df = quantity_df.reset_index(drop=True).set_index('structure')

        logger.info('Dataframe pulled: %s', quantity_df.columns.values.tolist())

        X, cell_matrix = self.extract_and_reduce_dimensions(quantity_df)
        plot_strings = self.make_plots(X, cell_matrix=cell_matrix)

        self.write_table(plot_strings, self.target_order)

    def extract_and_reduce_dimensions(self, quantity_df):
        # collect vector representations for every structure from (structure-target_quantity) pairs
        cell_matrix = []
        cell_classes = []
        for cell_id in quantity_df.index.unique():
            cell_df = quantity_df.loc[cell_id]
            cell_values = cell_df.set_index('target').loc[self.target_order].quantity.values
            cell_matrix.append(cell_values)

        cell_matrix = np.stack(cell_matrix)
        logger.info("Feature matrix created")

        # Preprocess
        pipe = make_pipeline(SimpleImputer(strategy="mean"), QuantileTransformer())
        X = pipe.fit_transform(cell_matrix.copy())

        # Fit UMAP to processed data
        manifold = umap.UMAP().fit(X)
        X_reduced = manifold.transform(X)

        logger.info("Finished umap transformation")

        return X_reduced, cell_matrix

    def make_plots(self, X_reduced, cell_matrix):
        """ Make scatter plots with color-coded values
        :param X_reduced: 2d-umap output to use as plot coordinates
        :param cell_matrix: original target quantity values to use for coloring """
        plots = []
        for target_idx, target_id in enumerate(self.target_order):
            f, ax = plt.subplots()  # figsize=(6, 5))

            points = ax.scatter(X_reduced[:, 0], X_reduced[:, 1], c=cell_matrix[:, target_idx], s=5, cmap=self.cmap,
                                alpha=0.7)
            f.colorbar(points)

            # source https://stackoverflow.com/questions/31492525/converting-matplotlib-png-to-base64-for-viewing-in-html-template
            # write to fictional file and then read the content back from it

            figfile = BytesIO()
            plt.savefig(figfile, format='svg')
            figfile.seek(0)  # rewind to beginning of file
            figdata_svg = base64.b64encode(figfile.getvalue())

            plots.append(figdata_svg)
            plt.close()
        return plots

    # def get_mask(self, cells, signature):
    #     value, multiindex = self.get_value_and_multiindex(signature)
    #     try:
    #         loc = cells.set_index(multiindex).index.get_loc(value)
    #     except KeyError:
    #         return np.asarray([False,] * cells.shape[0])
    #     if isinstance(loc, np.ndarray):
    #         return loc
    #     if isinstance(loc, slice):
    #         range1 = [False,]*(loc.start - 0)
    #         range2 = [True,]*(loc.stop - loc.start)
    #         range3 = [False,]*(cells.shape[0] - loc.stop)
    #         return np.asarray(range1 + range2 + range3)
    #     if isinstance(loc, int):
    #         return np.asarray([i == loc for i in range(cells.shape[0])])
    #     raise ValueError(f'Could not select by index: {multiindex}. Got: {loc}')
    #
    # def get_value_and_multiindex(self, signature):
    #     value = (1,) * len(signature['positive']) + (0,) * len(signature['negative'])
    #     if len(value) == 1:
    #         value = value[0]
    #     multiindex = [*signature['positive'], *signature['negative']]
    #     return value, multiindex

    def write_table(self, plot_strings, cases):
        if len(plot_strings) != len(cases):
            raise ValueError('Number of computed features not equal to number of cases.')
        df = pd.DataFrame(list(zip(cases, plot_strings)),
                          columns=['Target', 'PlotString'])

        bundle = [df, self.sample_identifier]
        with open(self.results_file, 'wb') as file:
            pickle.dump(bundle, file)
        logger.info('Computed metrics: %s', df.head())
        logger.info('Saved job output to file  %s', self.results_file)
