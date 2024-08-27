"""The core calculator for the UMAP dimensional reduction."""
import warnings
import pickle

from pandas import DataFrame  # type: ignore
import pandas.errors as pd_errors  # type: ignore
from psycopg import Cursor as PsycopgCursor

from umap import UMAP  # type: ignore
from sklearn.impute import SimpleImputer  # type: ignore
from sklearn.pipeline import make_pipeline  # type: ignore
from sklearn.preprocessing import QuantileTransformer  # type: ignore

from spatialprofilingtoolbox.workflow.common.sparse_matrix_puller import SparseMatrixPuller
from spatialprofilingtoolbox.db.accessors import CellsAccess
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

warnings.simplefilter(action='ignore', category=pd_errors.PerformanceWarning)
warnings.filterwarnings(action='ignore', message='n_jobs value 1 overridden to 1 by setting random_state. Use no seed for parallelism.')

from spatialprofilingtoolbox.workflow.common.umap_defaults import VIRTUAL_SAMPLE_SPEC1
from spatialprofilingtoolbox.workflow.common.umap_defaults import VIRTUAL_SAMPLE_SPEC2

logger = colorized_logger(__name__)

UMAP_POINT_LIMIT = 100000


class UMAPCreator:
    database_config_file: str | None
    study: str

    def __init__(self, database_config_file: str | None, study: str):
        self.database_config_file = database_config_file
        self.study = study

    def create(self) -> None:
        self._generate_and_write_reductions()

    def _generate_and_write_reductions(self) -> None:
        continuous, discrete = self.retrieve_feature_matrix_dense(cell_limit=UMAP_POINT_LIMIT)
        reduced = UMAPReducer.create_2d_point_cloud(continuous)
        self._write_to_database(reduced, discrete)

    def retrieve_feature_matrix_dense(self, cell_limit=None):
        sparse_df = self.retrieve_feature_matrix_sparse(cell_limit=cell_limit)
        continuous = UMAPCreator.sparse_to_dense(sparse_df, 'quantity')
        discrete = UMAPCreator.sparse_to_dense(sparse_df, 'discrete_value')
        continuous.sort_index(inplace=True)
        discrete.sort_index(inplace=True)
        return (continuous, discrete)

    def retrieve_feature_matrix_sparse(self, cell_limit=None):
        if cell_limit is None:
            raise ValueError('Need to choose a cell_limit.')
        logger.info(f'Retrieving cell data for "{self.study}".')
        with DBCursor(database_config_file=self.database_config_file, study=self.study) as cursor:
            cursor.execute('''
            SELECT
                eq.histological_structure,
                cs.symbol,
                eq.quantity,
                CASE WHEN eq.discrete_value='positive' THEN 1 ELSE 0 END discrete_value
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
            ''', (self.study, self.study, cell_limit))
            rows = cursor.fetchall()
        sparse_df = DataFrame(rows, columns=['structure', 'channel', 'quantity', 'discrete_value'])
        sparse_df = sparse_df.astype({'structure': str, 'channel': str, 'quantity': float, 'discrete_value': int})
        self.validate_all_structures_have_same_channels(sparse_df)
        logger.info('Dataframe pulled: %s', sparse_df.columns.values.tolist())
        return sparse_df

    @staticmethod
    def sparse_to_dense(sparse_df: DataFrame, values_column: str) -> DataFrame:
        logger.info(f'Converting sparse matrix to dense matrix. ({values_column})')
        dense_df = sparse_df.pivot(index='structure', columns=['channel'], values=[values_column])
        logger.info(f'Dense matrix ({values_column}) has size: {dense_df.shape}')
        return dense_df

    def validate_all_structures_have_same_channels(self, df) -> bool:
        if not (df.channel.value_counts() == len(df.structure.unique())).all():
            message = 'Cannot create a UMAP representation for study %s because given objects \
            have different sets of targets provided. Hence object representations have different \
            dimension which is incompatible with UMAP dimension reduction.'
            logger.error(message, self.study)
            raise ValueError(message % self.study)
        return True

    def _write_to_database(self, reduced, discrete: DataFrame) -> None:
        data_array = self._create_data_array(discrete)
        blob = bytearray()
        for histological_structure_id, entry in data_array.items():
            blob.extend(histological_structure_id.to_bytes(8, 'little'))
            blob.extend(entry.to_bytes(8, 'little'))
        centroid_data = {
            VIRTUAL_SAMPLE_SPEC2[0]: dict(tuple(
                zip(tuple(discrete.index.astype(int)), tuple(zip(reduced[:,0], reduced[:,1])))
            ))
        }
        logger.info('Saving UMAP centroids and feature matrix.')
        with DBCursor(database_config_file=self.database_config_file, study=self.study) as cursor:
            self._drop_existing_umap_cache(cursor)
            insert_query = '''
                INSERT INTO
                ondemand_studies_index (
                    specimen,
                    blob_type,
                    blob_contents)
                VALUES (%s, %s, %s) ;
            '''
            cursor.execute(insert_query, (*VIRTUAL_SAMPLE_SPEC1, blob))
            cursor.execute(insert_query, (*VIRTUAL_SAMPLE_SPEC2, pickle.dumps(centroid_data)))
        logger.info('Done.')

    def _drop_existing_umap_cache(self, cursor: PsycopgCursor):
        logger.info('  Dropping existing UMAP cache blobs.')
        delete_directive='''
        DELETE FROM ondemand_studies_index WHERE specimen=%s AND blob_type=%s;
        '''
        cursor.execute(delete_directive, VIRTUAL_SAMPLE_SPEC1)
        cursor.execute(delete_directive, VIRTUAL_SAMPLE_SPEC2)
        logger.info('  Done.')

    def _create_data_array(self, discrete: DataFrame) -> dict[int, int]:
        with DBCursor(database_config_file=self.database_config_file, study=self.study) as cursor:
            ordered = CellsAccess(cursor).get_ordered_feature_names()
        symbols = [('discrete_value', n.symbol) for n in ordered.names]
        logger.info(f'Using feature order: {[s[1] for s in symbols]}')
        discrete_ordered = discrete[symbols]
        data_array = {}
        for i, row in discrete_ordered.iterrows():
            binary = row.astype(int).to_numpy()
            data_array[int(i)] = SparseMatrixPuller._compress_bitwise_to_int(binary)
        return data_array


class UMAPReducer:
    """From dataframe create UMAP-reduced point clouds."""
    @staticmethod
    def create_2d_point_cloud(dense_df: DataFrame):
        normalized = UMAPReducer.preprocess_univariate_adjustments(dense_df)
        reduced = UMAPReducer.umap_reduce_to_2d(normalized)
        reduced_scaled = UMAPReducer.scale_up(reduced)
        return reduced_scaled

    @staticmethod
    def preprocess_univariate_adjustments(df):
        pipeline = make_pipeline(SimpleImputer(strategy="mean"), QuantileTransformer())
        return pipeline.fit_transform(df.copy())

    @staticmethod
    def umap_reduce_to_2d(array):
        manifold = UMAP(random_state=99, min_dist=0.2).fit(array)
        return manifold.transform(array)

    @staticmethod
    def scale_up(array):
        first = tuple(zip(array[0:5,0], array[0:5,1]))
        logger.info(f'First few points: {first}')
        size_x = max(array[:,0])
        size_y = max(array[:,1])
        scale = 5000 / min(size_x, size_y)
        scaled = scale * array
        first = tuple(zip(scaled[0:5,0], scaled[0:5,1]))
        logger.info(f'After scaling: {first}')
        return scaled
