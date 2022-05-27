
## number of slides
## number of cells
## average number of cells per slide

## average fraction, over slides
## standard deviation of fraction, over slides
## all of the above under compartmental or outcome assignment specialization
## extrema, high and low, sample identifier and value, for all of the above

REFRESH MATERIALIZED VIEW single_channel_diagnosis_breakdown_report;
REFRESH MATERIALIZED VIEW single_channel_all_diagnosis_breakdown_report;
REFRESH MATERIALIZED VIEW composite_diagnosis_breakdown_report;
REFRESH MATERIALIZED VIEW composite_all_diagnosis_breakdown_report;
REFRESH MATERIALIZED VIEW phenotyping_breakdown_report;

DROP MATERIALIZED VIEW phenotyping_breakdown_report;
DROP MATERIALIZED VIEW single_channel_diagnosis_breakdown_report;
DROP MATERIALIZED VIEW single_channel_all_diagnosis_breakdown_report;
DROP MATERIALIZED VIEW composite_diagnosis_breakdown_report;
DROP MATERIALIZED VIEW composite_all_diagnosis_breakdown_report;

CREATE MATERIALIZED VIEW single_channel_diagnosis_breakdown_report
AS
SELECT
    all_cells.study as study,
    'single channel' as multiplicity,
    all_cells.marker_symbol as phenotype,
    CAST(100 * number_positive / CAST(number_all_cells AS FLOAT) AS NUMERIC(7, 4)) as percent_positive,
    all_cells.diagnosis as diagnosis_specialization
FROM
    (
    SELECT
        sdmp.study as study,
        cs.symbol as marker_symbol,
        di.result as diagnosis,
        COUNT(*) as number_all_cells
    FROM
        expression_quantification eq
        LEFT JOIN
            chemical_species cs
        ON
            cs.identifier = eq.target
        LEFT JOIN histological_structure_identification hsi
        ON
            eq.histological_structure = hsi.histological_structure
        LEFT JOIN data_file df
        ON 
            hsi.data_source = df.sha256_hash
        LEFT JOIN specimen_data_measurement_process sdmp
        ON
            df.source_generation_process = sdmp.identifier
        LEFT JOIN specimen_collection_process scp
        ON
            sdmp.specimen = scp.specimen
        LEFT JOIN diagnosis di
        ON
            scp.source = di.subject
    GROUP BY
        sdmp.study,
        cs.symbol,
        di.result
    ) AS all_cells
LEFT JOIN
    (
    SELECT
        sdmp.study as study,
        cs.symbol as marker_symbol,
        di.result as diagnosis,
        COUNT(*) as number_positive
    FROM
        expression_quantification eq
        LEFT JOIN
            chemical_species cs
        ON
            cs.identifier = eq.target
        LEFT JOIN histological_structure_identification hsi
        ON
            eq.histological_structure = hsi.histological_structure
        LEFT JOIN data_file df
        ON 
            hsi.data_source = df.sha256_hash
        LEFT JOIN specimen_data_measurement_process sdmp
        ON
            df.source_generation_process = sdmp.identifier
        LEFT JOIN specimen_collection_process scp
        ON
            sdmp.specimen = scp.specimen
        LEFT JOIN diagnosis di
        ON
            scp.source = di.subject
    WHERE
        eq.discrete_value = 'positive'
    GROUP BY
        sdmp.study,
        cs.symbol,
        di.result
    ) AS positives_only
ON
    positives_only.study = all_cells.study
    AND
    positives_only.marker_symbol = all_cells.marker_symbol
    AND
    positives_only.diagnosis = all_cells.diagnosis
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
        LEFT JOIN
            chemical_species cs
        ON
            cs.identifier = eq.target
        LEFT JOIN histological_structure_identification hsi
        ON
            eq.histological_structure = hsi.histological_structure
        LEFT JOIN data_file df
        ON 
            hsi.data_source = df.sha256_hash
        LEFT JOIN specimen_data_measurement_process sdmp
        ON
            df.source_generation_process = sdmp.identifier
    GROUP BY
        sdmp.study,
        cs.symbol
    ) AS all_cells
LEFT JOIN
    (
    SELECT
        sdmp.study as study,
        cs.symbol as marker_symbol,
        COUNT(*) as number_positive
    FROM
        expression_quantification eq
        LEFT JOIN
            chemical_species cs
        ON
            cs.identifier = eq.target
        LEFT JOIN histological_structure_identification hsi
        ON
            eq.histological_structure = hsi.histological_structure
        LEFT JOIN data_file df
        ON 
            hsi.data_source = df.sha256_hash
        LEFT JOIN specimen_data_measurement_process sdmp
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
        LEFT JOIN
            cell_phenotype_criterion cpc
        ON
            eq.target = cpc.marker
        WHERE
            cpc.polarity = eq.discrete_value
        GROUP BY
            eq.histological_structure,
            cpc.cell_phenotype
        ) AS satisfied

    LEFT JOIN histological_structure_identification hsi
    ON
        satisfied.histological_structure = hsi.histological_structure
    LEFT JOIN data_file df
    ON 
        hsi.data_source = df.sha256_hash
    LEFT JOIN specimen_data_measurement_process sdmp
    ON
        df.source_generation_process = sdmp.identifier
    LEFT JOIN specimen_collection_process scp
    ON
        sdmp.specimen = scp.specimen
    LEFT JOIN diagnosis di
    ON
        scp.source = di.subject

    LEFT JOIN
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
LEFT JOIN cell_phenotype
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
        LEFT JOIN
            cell_phenotype_criterion cpc
        ON
            eq.target = cpc.marker
        WHERE
            cpc.polarity = eq.discrete_value
        GROUP BY
            eq.histological_structure,
            cpc.cell_phenotype
        ) AS satisfied

    LEFT JOIN histological_structure_identification hsi
    ON
        satisfied.histological_structure = hsi.histological_structure
    LEFT JOIN data_file df
    ON 
        hsi.data_source = df.sha256_hash
    LEFT JOIN specimen_data_measurement_process sdmp
    ON
        df.source_generation_process = sdmp.identifier

    LEFT JOIN
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
LEFT JOIN cell_phenotype
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
