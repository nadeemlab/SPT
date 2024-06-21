"""Queue of metrics to be computed as jobs."""

from attrs import define
from psycopg import Cursor as PsycopgCursor

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
                quantitative_feature_value_queue
                WHERE identifier IN
                    (SELECT qfvq.identifier FROM quantitative_feature_value_queue qfvq LIMIT 1)
                RETURNING feature, subject ;
                '''
                with DBCursor(database_config_file=self.database_config_file, study=study) as cursor:
                    cursor.execute(query)
                    rows = tuple(cursor.fetchall())
                    if len(rows) == 1:
                        row = rows[0]
                        return ComputationJobReference(int(row[0]), study, row[1])
                    cursor.execute('SELECT COUNT(*) FROM quantitative_feature_value_queue;')
                    count = int(tuple(cursor.fetchall())[0][0])
                    if count == 0:
                        studies_empty.add(study)
                        continue
        return None

    @staticmethod
    def _insert_jobs(cursor: PsycopgCursor, feature_specification: int) -> None:
        query = '''
        INSERT INTO quantitative_feature_value_queue
            (identifier, feature, subject)
        SELECT
            (
                SELECT
                CASE WHEN (SELECT COUNT(*) FROM quantitative_feature_value_queue) > 0
                THEN (SELECT MAX(CAST(identifier as integer)) FROM quantitative_feature_value_queue)
                ELSE 0 END
            ) + row_number() OVER (ORDER BY sq.specimen),
            %s,
            sq.specimen
        FROM ( %s ) sq ;
        ''' % (
            f"'{feature_specification}'",
            OnDemandProvider.relevant_specimens_query() % f"'{feature_specification}'",
        )
        cursor.execute(query)

    def _get_studies(self) -> tuple[str, ...]:
        with DBCursor(database_config_file=self.database_config_file) as cursor:
            cursor.execute('SELECT study FROM study_lookup ;')
            return tuple(map(lambda row: row[0], cursor.fetchall()))
