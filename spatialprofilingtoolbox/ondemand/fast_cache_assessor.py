"""Assesses presence of "fast cache" files, and creates/deletes as necessary."""

from subprocess import run as subprocess_run
from subprocess import CalledProcessError
from os import environ
from os import remove
from os import listdir
from os.path import isfile
from os.path import join
from os.path import isdir
from typing import cast
from json import loads as load_json_string
import re
from time import sleep

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import retrieve_study_names
from spatialprofilingtoolbox.workflow.common.structure_centroids import StructureCentroids
from spatialprofilingtoolbox.ondemand.defaults import EXPRESSIONS_INDEX_FILENAME
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)

class FastCacheAssessor:
    """Assess "fast cache"."""

    source_data_location: str
    centroids: dict[str, dict[str, list]]
    expressions_index: list[dict]

    def __init__(self, source_data_location: str):
        self.source_data_location = source_data_location

    def assess_and_act(self):
        up_to_date = self._cache_is_up_to_date()
        if not self.recreation_enabled():
            logger.info('Recreation not enabled, done assessing fast cache.')
            return

        if not up_to_date:
            self._clear()
            self._recreate()
        else:
            logger.info('Cache is basically as expected, not recreating.')

    def block_until_available(self):
        check_count = 0
        up_to_date = False
        while up_to_date is False:
            if check_count % 120 == 0:
                verbose=True
            else:
                verbose=False
            up_to_date = self._cache_is_up_to_date(verbose=verbose)
            if verbose:
                logger.debug('Waiting for cache to be available.')
            check_count += 1
            sleep(5)

    def _cache_is_up_to_date(self, verbose: bool = True) -> bool:
        if not self._check_files_present(verbose=verbose):
            return False
        self._retrieve_files()
        checkers = [
            self._check_study_sets,
            self._check_sample_sets,
        ]
        return all(checker() for checker in checkers)

    def _clear(self):
        logger.info('Deleting the fast cache files.')
        expressions_files = [
            f for f in listdir(self.source_data_location)
            if re.match(r'^expression_data_array\.[\d]+\.[\d]+\.bin$', f)
        ]
        scs = StructureCentroids()
        scs.set_data_directory(self.source_data_location)
        centroids_files = list(scs.get_all_centroids_pickle_files())
        for filename in centroids_files + [EXPRESSIONS_INDEX_FILENAME] + expressions_files:
            try:
                remove(join(self.source_data_location, filename))
                logger.info('Deleted %s .', filename)
            except FileNotFoundError:
                pass

    def _recreate(self):
        logger.info('Recreating fast cache files.')
        change_directory = f'cd {self.source_data_location}'
        if not isdir(self.source_data_location):
            raise RuntimeError(f'Directory does not exist: {self.source_data_location}')
        main_command = 'spt ondemand cache-expressions-data-array --database-config-file=none'
        commands = [change_directory, main_command]
        command = '; '.join(commands)
        logger.debug('Command is:')
        logger.debug(command)
        try:
            subprocess_run(command, shell=True, check=True)
        except CalledProcessError as exception:
            err = 'CalledProcessError'
            message = f'Received {err} during cache creation, probably insufficient available RAM.'
            logger.error(message)
            logger.info(str(exception))
            logger.info('Entering 2 hour indefinite sleep loop.')
            hour = 60 * 60
            while True:
                sleep(2 * hour)
                logger.info('Still sleeping.')

    def _check_files_present(self, verbose: bool = True) -> bool:
        files_present = {
            filename: isfile(join(self.source_data_location, filename))
            for filename in [EXPRESSIONS_INDEX_FILENAME]
        }
        centroids_present = StructureCentroids.already_exists(self.source_data_location, verbose=verbose)
        if verbose:
            for filename, present in files_present.items():
                indicator = 'present' if present else 'not present'
                logger.info('File %s is %s.', filename, indicator)
            if not centroids_present:
                logger.info('Centroids files not present.')
            else:
                logger.info('Centroids files are present.')
        return all(files_present.values()) and centroids_present

    def _check_study_sets(self) -> bool:
        return self._check_centroids_bundle_studies() and self._check_expressions_index_studies()

    def _retrieve_files(self):
        scs = StructureCentroids()
        scs.set_data_directory(self.source_data_location)
        scs.load_from_file()
        self.centroids = cast(dict[str, dict[str, list]], scs.get_studies())

        filename = join(self.source_data_location, EXPRESSIONS_INDEX_FILENAME)
        with open(filename, 'rt', encoding='utf-8') as file:
            self.expressions_index = load_json_string(file.read())['']

    def _check_centroids_bundle_studies(self):
        indexed_studies = self.centroids.keys()
        known_studies = self._retrieve_measurement_studies()
        known_measurement_studies = [row[1] for row in known_studies]
        log_expected_found(
            known_measurement_studies,
            indexed_studies,
            'Study "%s" not mentioned in centroids file.',
            '"%s" is mentioned in centroids file but not actually in database.',
            context='centroids',
        )
        return set(known_measurement_studies).issubset(set(indexed_studies))

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
        study_names = retrieve_study_names(None)
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
        indexed_samples = self.centroids[measurement_study].keys()
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
        index = [
            row for row in self.expressions_index
            if row['specimen measurement study name'] == measurement_study
        ][0]
        indexed_samples = [
            entry['specimen']
            for entry in index['expressions files']
        ]
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

    @staticmethod
    def recreation_enabled() -> bool:
        """If environment variable DISABLE_FAST_CACHE_RECREATION=1, the fast cache assessor will not
        do cache recreation, and it will not delete old cache. It will do only read operations.
        If this environment variable does not exist or is not equal to 1, recreation will be
        considered and possibly attempted.
        """
        key = 'DISABLE_FAST_CACHE_RECREATION'
        if key in environ:
            disable_fast_cache_recreation = environ[key] == '1'
        else:
            disable_fast_cache_recreation = False
        return not disable_fast_cache_recreation

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
