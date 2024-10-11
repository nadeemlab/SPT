"""Query for relevant active jobs."""

def select_active_jobs_query() -> str:
    retry_interval_seconds = 60 * 3
    max_retries = 3
    return '''
    SELECT * FROM (
        SELECT
            q2.feature, q2.subject, q2.computation_start
        FROM quantitative_feature_value_queue q2
        WHERE q2.computation_start IS NULL and q2.retries < %s
        UNION
        SELECT
            q3.feature, q3.subject, q3.computation_start
        FROM quantitative_feature_value_queue q3
        WHERE
            q3.computation_start IS NOT NULL AND
            now() - q3.computation_start > ( %s ) * INTERVAL '1' second AND
            q3.retries < %s
    ) AS activequeue ORDER BY computation_start NULLS FIRST
    ''' % (max_retries, retry_interval_seconds, max_retries)
