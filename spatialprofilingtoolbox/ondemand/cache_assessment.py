"""Assesses presence of "fast cache" files, and creates/deletes as necessary."""

from typing import cast
from json import loads as load_json_string
from time import sleep
from attr import define

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import retrieve_study_names
from spatialprofilingtoolbox.workflow.common.structure_centroids import StructureCentroids
from spatialprofilingtoolbox.workflow.common.cache_pulling import cache_pull
from spatialprofilingtoolbox.workflow.common.cache_pulling import umap_cache_pull
from spatialprofilingtoolbox.workflow.common.cache_pulling import compressed_payloads_cache_pull
from spatialprofilingtoolbox.workflow.common.cache_pulling import BROTLI_BLOB_TYPE
from spatialprofilingtoolbox.workflow.common.umap_defaults import VIRTUAL_SAMPLE
from spatialprofilingtoolbox.workflow.common.umap_defaults import VIRTUAL_SAMPLE_SPEC1
from spatialprofilingtoolbox.workflow.common.umap_defaults import VIRTUAL_SAMPLE_SPEC2
from spatialprofilingtoolbox.workflow.common.umap_defaults import VIRTUAL_SAMPLE_COMPRESSED
from spatialprofilingtoolbox.ondemand.compressed_matrix_writer import CompressedMatrixWriter
from spatialprofilingtoolbox.db.ondemand_studies_index import get_counts, retrieve_expressions_index
from spatialprofilingtoolbox.db.ondemand_studies_index import drop_cache_files
from spatialprofilingtoolbox.db.ondemand_studies_index import retrieve_indexed_samples
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)

@define
class CacheAssessorRecreator:
    database_config_file: str
    study: str

    def assess_and_act(self) -> None:
        if not self.is_up_to_date():
            self.clear()
            self.recreate()
        else:
            logger.info(f'{self.cache_specifier_name()} is up to date, not recreating.')

    def cache_specifier_name(self) -> str:
        raise NotImplementedError

    def is_up_to_date(self) -> bool:
        raise NotImplementedError

    def clear(self) -> None:
        logger.info(f'Deleting the {self.cache_specifier_name()}. ({self.study})')
        self._clear()

    def _clear(self) -> None:
        raise NotImplementedError

    def recreate(self) -> None:
        logger.info(f'Recreating the {self.cache_specifier_name()}. ({self.study})')
        self._recreate()

    def _recreate(self) -> None:
        raise NotImplementedError


class BinaryFeaturePositionsCacheManager(CacheAssessorRecreator):
    def cache_specifier_name(self) -> str:
        return 'Binary feature matrices and position data'

    def is_up_to_date(self) -> bool:
        writer = CompressedMatrixWriter(self.database_config_file)
        expressions_exist = writer.expressions_indices_already_exist(study=self.study)
        structure_centroids = StructureCentroids(self.database_config_file)
        centroids_present = structure_centroids.centroids_exist(study=self.study)
        if not expressions_exist:
            logger.info(f'Did not find expressions indices. ({self.study})')
        else:
            logger.info('Found expressions index file(s).')
        if not centroids_present:
            logger.info('Databased centroids files not present.')
        else:
            logger.info('Databased centroids files are present.')
        return expressions_exist and centroids_present

    def _clear(self):
        drop_cache_files(self.database_config_file, 'feature_matrix', study=self.study)
        drop_cache_files(self.database_config_file, 'expressions_index', study=self.study)
        drop_cache_files(self.database_config_file, 'centroids', study=self.study)

    def _recreate(self):
        cache_pull(self.database_config_file, study=self.study)


class UMAPCacheManager(CacheAssessorRecreator):
    def cache_specifier_name(self) -> str:
        return 'UMAP binary format data'

    def is_up_to_date(self) -> bool:
        with DBCursor(study=self.study, database_config_file=self.database_config_file) as cursor:
            query = '''
            SELECT COUNT(*)
            FROM ondemand_studies_index
            WHERE specimen=%s AND blob_type=%s ;
            '''
            cursor.execute(query, VIRTUAL_SAMPLE_SPEC1)
            count = cursor.fetchall()[0][0]
            if count != 1:
                logger.info(f'Study {self.study} lacks "UMAP virtual sample feature matrix".')
                return False
            cursor.execute(query, VIRTUAL_SAMPLE_SPEC2)
            count = cursor.fetchall()[0][0]
            if count != 1:
                logger.info(f'Study {self.study} lacks "UMAP virtual sample centroids".')
                return False
        return True

    def _clear(self) -> None:
        drop_cache_files(self.database_config_file, VIRTUAL_SAMPLE_SPEC1[1], study=self.study)
        drop_cache_files(self.database_config_file, VIRTUAL_SAMPLE_SPEC2[1], study=self.study)

    def _recreate(self) -> None:
        umap_cache_pull(self.database_config_file, study=self.study)


class CompressedPayloadsCacheManager(CacheAssessorRecreator):
    def cache_specifier_name(self) -> str:
        return 'Compressed binary per-sample payloads'

    def is_up_to_date(self) -> bool:
        with DBCursor(study=self.study, database_config_file=self.database_config_file) as cursor:
            number_specimens = self._get_number_specimens(cursor)
            query = '''
            SELECT COUNT(*)
            FROM ondemand_studies_index
            WHERE blob_type=%s ;
            '''
            cursor.execute(query, (BROTLI_BLOB_TYPE,))
            count = cursor.fetchall()[0][0]
            if count != number_specimens:
                logger.info(f'Study {self.study} lacks some compressed payloads.')
                return False
            query = '''
            SELECT COUNT(*)
            FROM ondemand_studies_index
            WHERE specimen=%s AND blob_type=%s ;
            '''
            cursor.execute(query, (VIRTUAL_SAMPLE, VIRTUAL_SAMPLE_COMPRESSED))
            count = cursor.fetchall()[0][0]
            if count != 1:
                logger.info(f'Study {self.study} lacks "UMAP compressed virtual sample".')
                return False
        return True

    def _clear(self) -> None:
        drop_cache_files(self.database_config_file, BROTLI_BLOB_TYPE, study=self.study)
        drop_cache_files(self.database_config_file, VIRTUAL_SAMPLE_COMPRESSED, study=self.study)

    def _recreate(self) -> None:
        compressed_payloads_cache_pull(self.database_config_file, study=self.study)

    def _get_number_specimens(self, cursor) -> int:
        cursor.execute('''
            SELECT COUNT(*)
            FROM specimen_data_measurement_process sdmp;
        ''')
        return int(cursor.fetchall()[0][0])


class CacheAssessment:
    """Assess derivative cache files, recreate from source datasets if necessary."""
    database_config_file: str | None
    study: str

    def __init__(self, database_config_file: str | None, study: str | None=None):
        self.database_config_file = database_config_file
        if study is None:
            raise ValueError('You must supply a study for cache creation. The older workflow that '
                             'worked on all studies at once is deprecated.')
        self.study = cast(str, study)

    def assess_and_act(self):
        for Assessor in [
            BinaryFeaturePositionsCacheManager,
            UMAPCacheManager,
            CompressedPayloadsCacheManager,
        ]:
            assessor = cast(CacheAssessorRecreator, Assessor(self.database_config_file, self.study))
            assessor.assess_and_act()
