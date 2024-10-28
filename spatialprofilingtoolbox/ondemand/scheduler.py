"""Queue of metrics to be computed as jobs."""

from attrs import define
from psycopg import Cursor as PsycopgCursor

from spatialprofilingtoolbox.ondemand.queue_query import select_active_jobs_query
from spatialprofilingtoolbox.ondemand.feature_computation_timeout import feature_computation_timeout_handler
from spatialprofilingtoolbox.ondemand.providers.provider import OnDemandProvider
from spatialprofilingtoolbox.ondemand.job_reference import ComputationJobReference
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import DBConnection
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


@define
class MetricComputationScheduler:
    """
    When a request for computation of some feature is received by the application, first the
    feature specification is written to the database, then this class should be used to "schedule"
    each of the values for computation.

    Workers can then use the pop function to remove one such job from the queue, before beginning
    work on the job.
    """
    database_config_file: str | None
    cursor: PsycopgCursor | None = None

    def schedule_feature_computation(self, study: str, feature_specification: int) -> None:
        with DBCursor(database_config_file=self.database_config_file, study=study) as cursor:
            self._insert_jobs(cursor, feature_specification)
        NORMAL_FEATURE_COMPUTATION_TIMEOUT = 60 * 10
        feature_computation_timeout_handler(str(feature_specification), study, NORMAL_FEATURE_COMPUTATION_TIMEOUT)
        self._broadcast_queue_activity()

    def _broadcast_queue_activity(self) -> None:
        logger.debug('Notifying queue activity channel that there are new items.')
        with DBConnection(database_config_file=self.database_config_file) as connection:
            connection.execute('NOTIFY new_items_in_queue ;')

    def pop_uncomputed(self) -> ComputationJobReference | None:
        studies = self._get_studies()
        number_studies = len(studies)
        studies_empty: set[str] = set([])
        while len(studies_empty) < number_studies:
            for study in set(studies).difference(studies_empty):
                query = '''
                DELETE FROM
                quantitative_feature_value_queue q1
                USING (
                    %s
                    LIMIT 1
                ) q
                WHERE q1.feature=q.feature AND q1.subject=q.subject
                RETURNING q1.feature, q1.subject, q1.computation_start, q1.retries ;
                ''' % select_active_jobs_query()
                with DBCursor(database_config_file=self.database_config_file, study=study) as cursor:
                    cursor.execute(query)
                    rows = tuple(cursor.fetchall())
                    if len(rows) == 1:
                        row = rows[0]
                        feature = int(row[0])
                        sample = str(row[1])
                        computation_start = row[2]
                        retries = int(row[3])
                        if computation_start is not None:
                            new_retries = retries + 1
                            logger.debug(f'Retrying due to assumed failure, iteration {new_retries}, ({feature}, {sample}).')
                        else:
                            new_retries = retries
                        cursor.execute('''
                            INSERT INTO quantitative_feature_value_queue
                                (feature, subject, computation_start, retries)
                            VALUES(
                                %s, %s, now(), %s
                            )
                            ''',
                            (feature, sample, new_retries)
                        )
                        return ComputationJobReference(feature, study, sample)
                    studies_empty.add(study)
                    continue
        return None

    @staticmethod
    def _insert_jobs(cursor: PsycopgCursor, feature_specification: int) -> None:
        query = '''
        INSERT INTO quantitative_feature_value_queue
            (feature, subject, computation_start, retries)
        SELECT
            %s, sq.specimen, NULL, 0
        FROM ( %s ) sq
        ON CONFLICT DO NOTHING ;
        ''' % (
            f"'{feature_specification}'",
            OnDemandProvider.relevant_specimens_query() % f"'{feature_specification}'",
        )
        cursor.execute(query)

    def _get_studies(self) -> tuple[str, ...]:
        with DBCursor(database_config_file=self.database_config_file) as cursor:
            cursor.execute('SELECT study FROM study_lookup ;')
            return tuple(map(lambda row: row[0], cursor.fetchall()))
