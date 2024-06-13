"""Queue of metrics to be computed as jobs."""

from attrs import define
from psycopg2.extensions import cursor as Psycopg2Cursor

from spatialprofilingtoolbox.ondemand.providers.pending_provider import PendingProvider
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import DBConnection

@define
class ComputationJobReference:
    feature_specification: int
    study: str
    sample: str


@define
class MetricComputationScheduler:
    """
    When a request for computation of some feature is received by the application, first the
    feature specification is written to the database, then this class should be used to "schedule"
    each of the values for computation.

    Workers can then use the pop function to remove one such job from the queue, before beginning
    work on the job.
    """
    database_config_file: str
    cursor: Psycopg2Cursor | None = None

    def schedule_feature_computation(self, study: str, feature_specification: int) -> None:
        with DBCursor(database_config_file=self.database_config_file, study=study) as cursor:
            self._insert_jobs(cursor, feature_specification)
            self._broadcast_queue_activity()

    def _broadcast_queue_activity(self) -> None:
        with DBConnection(database_config_file=self.database_config_file) as connection:
            connection.execute("NOTIFY queue_activity, 'new items' ;")

    def pop_uncomputed(self) -> ComputationJobReference | None:
        for study in self._get_studies():
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
                if len(rows) == 0:
                    continue
                row = rows[0]
                return ComputationJobReference(int(row[0]), study, row[1])
        return None

    @staticmethod
    def _insert_jobs(cursor: Psycopg2Cursor, feature_specification: int) -> None:
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
            PendingProvider.relevant_specimens_query() % f"'{feature_specification}'",
        )
        cursor.execute(query)

    def _get_studies(self) -> tuple[str, ...]:
        with DBCursor(database_config_file=self.database_config_file) as cursor:
            cursor.execute('SELECT study FROM study_lookup ;')
            return tuple(map(lambda row: row[0], cursor.fetchall()))
