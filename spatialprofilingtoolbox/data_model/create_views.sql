
CREATE MATERIALIZED VIEW cell_count_by_study_specimen AS
SELECT
    sdmp.study as study,
    sdmp.specimen as specimen,
    COUNT(*) as cell_count
FROM
    histological_structure_identification hsi
    JOIN histological_structure hs ON
        hsi.histological_structure = hs.identifier
    JOIN data_file df ON 
        hsi.data_source = df.sha256_hash
    JOIN specimen_data_measurement_process sdmp ON
        df.source_generation_process = sdmp.identifier
WHERE
    hs.anatomical_entity = 'cell'
GROUP BY
    sdmp.study,
    sdmp.specimen
;

CREATE MATERIALIZED VIEW marker_positive_cell_count_by_study_specimen AS
SELECT
    sdmp.study as study,
    sdmp.specimen as specimen,
    cs.symbol as marker_symbol,
    COUNT(*) as cell_count
FROM
    expression_quantification eq
    JOIN histological_structure_identification hsi ON
        eq.histological_structure = hsi.histological_structure
    JOIN histological_structure hs ON
        eq.histological_structure = hs.identifier
    JOIN data_file df ON 
        hsi.data_source = df.sha256_hash
    JOIN specimen_data_measurement_process sdmp ON
        df.source_generation_process = sdmp.identifier
    JOIN chemical_species cs ON
        eq.target = cs.identifier
WHERE
    hs.anatomical_entity = 'cell'
AND
    eq.discrete_value = 'positive'
GROUP BY
    sdmp.study,
    sdmp.specimen,
    cs.symbol
;

CREATE VIEW fraction_by_marker_study_specimen AS
SELECT
    cc.study as study,
    cc.specimen as specimen,
    mpcc.marker_symbol as marker_symbol,
    100 * mpcc.cell_count / CAST(cc.cell_count AS FLOAT) as percent_positive
FROM
    cell_count_by_study_specimen cc
    JOIN marker_positive_cell_count_by_study_specimen mpcc ON
        cc.study = mpcc.study
        AND
        cc.specimen = mpcc.specimen
;

CREATE VIEW fraction_stats_by_marker_study AS
SELECT
    f.study as study,
    f.marker_symbol as symbol,
    CAST(AVG(f.percent_positive) AS NUMERIC(7, 4)) as average_percent,
    CAST(STDDEV(f.percent_positive) AS NUMERIC(7, 4)) as standard_deviation_of_percents
FROM
    fraction_by_marker_study_specimen f
GROUP BY
    f.study,
    f.marker_symbol
;

CREATE VIEW fraction_stats_by_marker_study_assessment AS
SELECT
    f.study as study,
    f.marker_symbol as symbol,
    hap.assay as assay,
    hap.result as assessment,
    CAST(AVG(f.percent_positive) AS NUMERIC(7, 4)) as average_percent,
    CAST(STDDEV(f.percent_positive) AS NUMERIC(7, 4)) as standard_deviation_of_percents
FROM
    fraction_by_marker_study_specimen f
    JOIN histology_assessment_process hap ON
        f.specimen = hap.slide
GROUP BY
    f.study,
    f.marker_symbol,
    hap.assay,
    hap.result
;


-- Warning: Below should really not mention subject directly, as above, but go through an histology assessment process. In your example data you need to move the subject-level stuff (wrongly attributed) to specimen level.
CREATE VIEW fraction_stats_by_marker_study_diagnosis_fake AS
SELECT
    f.study as study,
    f.marker_symbol as symbol,
    di.result as diagnosis,
    CAST(AVG(f.percent_positive) AS NUMERIC(7, 4)) as average_percent,
    CAST(STDDEV(f.percent_positive) AS NUMERIC(7, 4)) as standard_deviation_of_percents
FROM
    fraction_by_marker_study_specimen f
    JOIN specimen_collection_process scp ON
        f.specimen = scp.specimen
    JOIN diagnosis di ON
        scp.source = di.subject
GROUP BY
    f.study,
    f.marker_symbol,
    di.result
;
