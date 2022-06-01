
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
    100 * mpcc.cell_count / cc.cell_count as percent_positive
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


--Below are to be deprecated
CREATE VIEW positive_cell_counts_by_marker_and_diagnosis
AS
SELECT
    sdmp.study as study,
    cs.symbol as marker_symbol,
    di.result as diagnosis,
    COUNT(*) as number_positive
FROM
    expression_quantification eq
    JOIN
        chemical_species cs
    ON
        cs.identifier = eq.target
    JOIN histological_structure_identification hsi
    ON
        eq.histological_structure = hsi.histological_structure
    JOIN data_file df
    ON 
        hsi.data_source = df.sha256_hash
    JOIN specimen_data_measurement_process sdmp
    ON
        df.source_generation_process = sdmp.identifier
    JOIN specimen_collection_process scp
    ON
        sdmp.specimen = scp.specimen
    JOIN diagnosis di
    ON
        scp.source = di.subject
WHERE
    eq.discrete_value = 'positive'
GROUP BY
    sdmp.study,
    cs.symbol,
    di.result
;

CREATE MATERIALIZED VIEW single_channel_diagnosis_breakdown_report
AS
SELECT
    all_cells.study as study,
    'single channel' as multiplicity,
    all_cells.marker_symbol as phenotype,
    CAST(100 * number_positive / CAST(number_all_cells AS FLOAT) AS NUMERIC(7, 4)) as percent_positive,
    all_cells.diagnosis as diagnosis_specialization
FROM cell_counts_by_marker_and_diagnosis cc
JOIN positive_cell_counts_by_marker_and_diagnosis pcc
ON
    pcc.study = cc.study
    AND
    pcc.marker_symbol = cc.marker_symbol
    AND
    pcc.diagnosis = cc.diagnosis
;

CREATE MATERIALIZED VIEW single_channel_all_diagnosis_breakdown_report
AS
SELECT
    all_cells.study as study,
    'single channel' as multiplicity,
    all_cells.marker_symbol as phenotype,
    CAST(100 * number_positive / CAST(number_all_cells AS FLOAT) AS NUMERIC(7, 4)) as percent_positive,
    '<any>' as diagnosis_specialization
FROM
    (
    SELECT
        sdmp.study as study,
        cs.symbol as marker_symbol,
        COUNT(*) as number_all_cells
    FROM
        expression_quantification eq
        JOIN
            chemical_species cs
        ON
            cs.identifier = eq.target
        JOIN histological_structure_identification hsi
        ON
            eq.histological_structure = hsi.histological_structure
        JOIN data_file df
        ON 
            hsi.data_source = df.sha256_hash
        JOIN specimen_data_measurement_process sdmp
        ON
            df.source_generation_process = sdmp.identifier
    GROUP BY
        sdmp.study,
        cs.symbol
    ) AS all_cells
JOIN
    (
    SELECT
        sdmp.study as study,
        cs.symbol as marker_symbol,
        COUNT(*) as number_positive
    FROM
        expression_quantification eq
        JOIN
            chemical_species cs
        ON
            cs.identifier = eq.target
        JOIN histological_structure_identification hsi
        ON
            eq.histological_structure = hsi.histological_structure
        JOIN data_file df
        ON 
            hsi.data_source = df.sha256_hash
        JOIN specimen_data_measurement_process sdmp
        ON
            df.source_generation_process = sdmp.identifier
    WHERE
        eq.discrete_value = 'positive'
    GROUP BY
        sdmp.study,
        cs.symbol
    ) AS positives_only
ON
    positives_only.study = all_cells.study    
    AND
    positives_only.marker_symbol = all_cells.marker_symbol
;

CREATE MATERIALIZED VIEW composite_diagnosis_breakdown_report
AS
SELECT
    phenotype_frequency.study as study,
    'composite' as multiplicity,
    cell_phenotype.symbol as phenotype,
    CAST(100 * phenotype_frequency.frequency / CAST( (SELECT COUNT(*) FROM histological_structure) AS FLOAT) AS NUMERIC(7, 4)) as percent_positive,
    phenotype_frequency.diagnosis_result as diagnosis_specialization
FROM
    (
    SELECT
        sdmp.study as study,
        satisfied.cell_phenotype_identifier as cell_phenotype_identifier,
        di.result as diagnosis_result,
        COUNT(*) as frequency
    FROM
        (
        SELECT
            eq.histological_structure as histological_structure,
            cpc.cell_phenotype as cell_phenotype_identifier,
            COUNT(*) as number_criteria_satisfied
        FROM
            expression_quantification eq
        JOIN
            cell_phenotype_criterion cpc
        ON
            eq.target = cpc.marker
        WHERE
            cpc.polarity = eq.discrete_value
        GROUP BY
            eq.histological_structure,
            cpc.cell_phenotype
        ) AS satisfied

    JOIN histological_structure_identification hsi
    ON
        satisfied.histological_structure = hsi.histological_structure
    JOIN data_file df
    ON 
        hsi.data_source = df.sha256_hash
    JOIN specimen_data_measurement_process sdmp
    ON
        df.source_generation_process = sdmp.identifier
    JOIN specimen_collection_process scp
    ON
        sdmp.specimen = scp.specimen
    JOIN diagnosis di
    ON
        scp.source = di.subject

    JOIN
        (
        SELECT
            cpc.cell_phenotype as cell_phenotype_identifier,
            COUNT(*) as number_all_criteria
        FROM
            cell_phenotype_criterion cpc
        GROUP BY
            cpc.cell_phenotype
        ) AS all_criteria
    ON
        satisfied.cell_phenotype_identifier = all_criteria.cell_phenotype_identifier
    WHERE
        satisfied.number_criteria_satisfied = all_criteria.number_all_criteria
    GROUP BY
        sdmp.study,
        satisfied.cell_phenotype_identifier,
        di.result
    ) AS phenotype_frequency
JOIN cell_phenotype
ON
    phenotype_frequency.cell_phenotype_identifier = cell_phenotype.identifier 
;

CREATE MATERIALIZED VIEW composite_all_diagnosis_breakdown_report
AS
SELECT
    phenotype_frequency.study as study,
    'composite' as multiplicity,
    cell_phenotype.symbol as phenotype,
    CAST(100 * phenotype_frequency.frequency / CAST( (SELECT COUNT(*) FROM histological_structure) AS FLOAT) AS NUMERIC(7, 4)) as percent_positive,
    '<any>' as diagnosis_specialization
FROM
    (
    SELECT
        sdmp.study as study,
        satisfied.cell_phenotype_identifier as cell_phenotype_identifier,
        COUNT(*) as frequency
    FROM
        (
        SELECT
            eq.histological_structure as histological_structure,
            cpc.cell_phenotype as cell_phenotype_identifier,
            COUNT(*) as number_criteria_satisfied
        FROM
            expression_quantification eq
        JOIN
            cell_phenotype_criterion cpc
        ON
            eq.target = cpc.marker
        WHERE
            cpc.polarity = eq.discrete_value
        GROUP BY
            eq.histological_structure,
            cpc.cell_phenotype
        ) AS satisfied

    JOIN histological_structure_identification hsi
    ON
        satisfied.histological_structure = hsi.histological_structure
    JOIN data_file df
    ON 
        hsi.data_source = df.sha256_hash
    JOIN specimen_data_measurement_process sdmp
    ON
        df.source_generation_process = sdmp.identifier

    JOIN
        (
        SELECT
            cpc.cell_phenotype as cell_phenotype_identifier,
            COUNT(*) as number_all_criteria
        FROM
            cell_phenotype_criterion cpc
        GROUP BY
            cpc.cell_phenotype
        ) AS all_criteria
    ON
        satisfied.cell_phenotype_identifier = all_criteria.cell_phenotype_identifier
    WHERE
        satisfied.number_criteria_satisfied = all_criteria.number_all_criteria
    GROUP BY
        sdmp.study,
        satisfied.cell_phenotype_identifier
    ) AS phenotype_frequency
JOIN cell_phenotype
ON
    phenotype_frequency.cell_phenotype_identifier = cell_phenotype.identifier 
;

CREATE MATERIALIZED VIEW phenotyping_breakdown_report
AS
SELECT
    agg.study,
    agg.multiplicity,
    agg.phenotype,
    agg.percent_positive,
    agg.diagnosis_specialization
FROM
    (
    (SELECT * FROM single_channel_diagnosis_breakdown_report)
    UNION
    (SELECT * FROM single_channel_all_diagnosis_breakdown_report)
    UNION
    (SELECT * FROM composite_diagnosis_breakdown_report)
    UNION
    (SELECT * FROM composite_all_diagnosis_breakdown_report)
    ORDER BY
        study,
        multiplicity DESC,
        phenotype,
        diagnosis_specialization
    ) as agg
;
