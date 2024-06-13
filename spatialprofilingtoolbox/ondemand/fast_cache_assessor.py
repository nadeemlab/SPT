"""Assesses presence of "fast cache" files, and creates/deletes as necessary."""

from typing import cast
from json import loads as load_json_string
from time import sleep

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import retrieve_study_names
from spatialprofilingtoolbox.workflow.common.structure_centroids import StructureCentroids
from spatialprofilingtoolbox.workflow.common.cache_pulling import cache_pull
from spatialprofilingtoolbox.ondemand.compressed_matrix_writer import CompressedMatrixWriter
from spatialprofilingtoolbox.db.ondemand_studies_index import retrieve_expressions_index
from spatialprofilingtoolbox.db.ondemand_studies_index import drop_cache_files
from spatialprofilingtoolbox.db.ondemand_studies_index import retrieve_indexed_samples
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)

class FastCacheAssessor:
    """Assess "fast cache"."""
    database_config_file: str | None
    study: str | None
    centroids: dict[str, dict[str, list]]
    expressions_index: list[dict]

    def __init__(self, database_config_file: str | None, study: str | None=None):
        self.database_config_file = database_config_file
        self.study = study

    def assess_and_act(self):
        up_to_date = self._cache_is_up_to_date()
        if not up_to_date:
            self._clear()
            self._recreate()
        else:
            logger.info('Cache is basically as expected, not recreating.')

    def block_until_available(self):
        check_count = 0
        up_to_date = False
        while up_to_date is False:
            verbose = (check_count % 120 == 0)
            up_to_date = self._cache_is_up_to_date(verbose=verbose)
            if up_to_date:
                break
            if verbose:
                logger.debug('Waiting for cache to be available.')
            check_count += 1
            sleep(5)

    def _cache_is_up_to_date(self, verbose: bool = True) -> bool:
        if not self._check_databased_files_present(verbose=verbose):
            return False
        self._do_caching()
        checkers = [
            self._check_study_sets,
            self._check_sample_sets,
        ]
        return all(checker() for checker in checkers)

    def _get_study_indicator(self):
        return '' if self.study is None else f'({self.study})'

    def _clear(self):
        logger.info(f'Deleting the databased fast cache files. {self._get_study_indicator()}')
        drop_cache_files(self.database_config_file, 'feature_matrix', study=self.study)
        drop_cache_files(self.database_config_file, 'expressions_index', study=self.study)
        drop_cache_files(self.database_config_file, 'centroids', study=self.study)

    def _recreate(self):
        logger.info(f'Recreating databased fast cache files. {self._get_study_indicator()}')
        cache_pull(self.database_config_file, study=self.study)

    def _check_databased_files_present(self, verbose: bool = True) -> bool:
        writer = CompressedMatrixWriter(self.database_config_file)
        expressions_exist = writer.expressions_indices_already_exist(study=self.study)
        structure_centroids = StructureCentroids(self.database_config_file)
        centroids_present = structure_centroids.centroids_exist(study=self.study)
        if verbose:
            if not expressions_exist:
                logger.info(f'Did not find expressions indices. {self._get_study_indicator()}')
            else:
                logger.info('Found expressions index file(s).')
            if not centroids_present:
                logger.info('Databased centroids files not present.')
            else:
                logger.info('Databased centroids files are present.')
        return expressions_exist and centroids_present

    def _check_study_sets(self) -> bool:
        return self._check_centroids_bundle_studies() and self._check_expressions_index_studies()

    def _do_caching(self):
        scs = StructureCentroids(self.database_config_file)
        scs.load_from_db(study=self.study)
        self.centroids = cast(dict[str, dict[str, list]], scs.get_studies())
        self.expressions_index = []
        if self.study is None:
            studies = tuple(retrieve_study_names(self.database_config_file))
        else:
            studies = (self.study,)
        for study in studies:
            blob = retrieve_expressions_index(self.database_config_file, study)
            self.expressions_index.extend(load_json_string(blob)[''])

    def _check_centroids_bundle_studies(self):
        indexed_studies = self.centroids.keys()
        if self.study is None:
            known_studies = tuple(retrieve_study_names(self.database_config_file))
        else:
            known_studies = (self.study,)
        log_expected_found(
            known_studies,
            indexed_studies,
            'Study "%s" not mentioned in centroids file.',
            '"%s" is mentioned in centroids file but not actually in database.',
            context='centroids',
        )
        return set(known_studies).issubset(set(indexed_studies))

    def _check_expressions_index_studies(self):
        indexed_measurement_studies = [
            row['specimen measurement study name']
            for row in self.expressions_index
        ]
        known_studies = self._retrieve_measurement_studies()
        known_measurement_studies = [row[1] for row in known_studies]
        log_expected_found(
            known_measurement_studies,
            indexed_measurement_studies,
            'Study "%s" not mentioned in expressions index.',
            '"%s" is mentioned in expressions index but not actually in database.',
            context='expressions index',
        )
        return set(known_measurement_studies).issubset(set(indexed_measurement_studies))

    def _retrieve_measurement_studies(self) -> list[tuple[str, str]]:
        if self.study is None:
            study_names = tuple(retrieve_study_names(None))
        else:
            study_names = (self.study,)
        studies = []
        for study in study_names:
            with DBCursor(study=study) as cursor:
                cursor.execute('SELECT name FROM specimen_measurement_study ;')
                rows = cursor.fetchall()
                studies.extend([(study, row[0]) for row in rows])
        return studies

    def _check_sample_sets(self) -> bool:
        return self._check_sample_sets_centroids() and self._check_sample_sets_expressions_index()

    def _check_sample_sets_centroids(self):
        return all(
            self._check_centroids_samples(study, measurement_study)
            for study, measurement_study in self._retrieve_measurement_studies()
        )

    def _check_centroids_samples(self, study: str, measurement_study: str) -> bool:
        indexed_samples = self.centroids[study].keys()
        known_samples = self._retrieve_known_samples_measurement(study, measurement_study)
        log_expected_found(
            known_samples,
            indexed_samples,
            'Sample "%s" not mentioned in centroids file.',
            'Sample "%s" is mentioned in centroids file, but is not actually in database?',
            context='centroids',
        )
        return set(known_samples).issubset(set(indexed_samples))

    def _check_sample_sets_expressions_index(self):
        return all(
            self._check_expressions_index_samples(study, measurement_study)
            for study, measurement_study in self._retrieve_measurement_studies()
        )

    def _check_expressions_index_samples(self, study: str, measurement_study: str) -> bool:
        indexed_samples = retrieve_indexed_samples(cast(str, self.database_config_file), study)
        known_samples = self._retrieve_known_samples_measurement(study, measurement_study)
        log_expected_found(
            known_samples,
            indexed_samples,
            'Sample "%s" not mentioned in expressions index.',
            'Sample "%s" is mentioned in centroids file, but is not actually in database?',
            context='expressions index',
        )
        return set(known_samples).issubset(set(indexed_samples))

    def _retrieve_known_samples_measurement(self, study: str, measurement_study: str) -> list[str]:
        with DBCursor(study=study) as cursor:
            cursor.execute('''
            SELECT specimen FROM specimen_data_measurement_process sdmp
            WHERE sdmp.study=%s
            ''', (measurement_study,))
            rows = cursor.fetchall()
        return [row[0] for row in rows]


def log_expected_found(set1, set2, message1, message2, context: str=''):
    """Logs error message1 (one formattable argument) for each element of set1 (expected) that is
    missing from set2 (found).
    Also logs warning message2 for each element of set2 (found) that is not present in set1
    (expected).
    """
    matches = set(set1).intersection(set(set2))
    message = 'Elements found as expected: "%s".'
    if context != '':
        message = message + f' ({context}).'
    logger.info(message, abbreviate_list(list(matches)))
    for element in set(set1).difference(set(set2)):
        logger.error(message1, element)
    for element in set(set2).difference(set(set1)):
        logger.warning(message2, element)


def abbreviate_list(items: list[str]):
    if len(items) > 5:
        return items[0:5] + [f'... ({len(items)} total items)']
    return items
