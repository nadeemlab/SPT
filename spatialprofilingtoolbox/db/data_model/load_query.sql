SELECT
SUM(
  (
    xpath(
      '/row/c/text()',
      query_to_xml(
        format(
          'select count(*) as c from %I.%I where retries=0',
          schema_name,
          'quantitative_feature_value_queue'
        ),
        FALSE,
        TRUE,
        ''
      )
    )
  )[1]::text::int
) as total_jobs_in_queue
FROM
  default_study_lookup.study_lookup
;
