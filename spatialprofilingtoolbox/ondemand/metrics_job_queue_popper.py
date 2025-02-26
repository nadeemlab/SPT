"""Queue of metrics to be computed as jobs."""

from spatialprofilingtoolbox.ondemand.queue_query import select_active_jobs_query
from spatialprofilingtoolbox.ondemand.job_reference import ComputationJobReference
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class MetricsJobQueuePopper:
    @classmethod
    def pop_uncomputed(cls) -> ComputationJobReference | None:
        studies = cls._get_studies()
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
                with DBCursor(database_config_file=None, study=study) as cursor:
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

    @classmethod
    def _get_studies(cls) -> tuple[str, ...]:
        with DBCursor(database_config_file=None) as cursor:
            cursor.execute('SELECT study FROM study_lookup ;')
            return tuple(map(lambda row: row[0], cursor.fetchall()))
