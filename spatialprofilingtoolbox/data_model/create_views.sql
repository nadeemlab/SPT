
-- Single phenotype counts
CREATE MATERIALIZED VIEW marker_positive_cell_count_by_study_specimen AS
SELECT
    sdmp.study as study,
    sdmp.specimen as specimen,
    'single' as multiplicity,
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

-- Composite phenotype counts
CREATE VIEW cells_count_criteria_satisfied AS
SELECT
    eq.histological_structure as histological_structure,
    cpc.cell_phenotype as cell_phenotype_identifier,
    COUNT(*) as number_criteria_satisfied
FROM
    expression_quantification eq
    JOIN histological_structure hs ON
        eq.histological_structure = hs.identifier
    JOIN cell_phenotype_criterion cpc ON
        eq.target = cpc.marker
WHERE
    cpc.polarity = eq.discrete_value
AND
    hs.anatomical_entity = 'cell'
GROUP BY
    eq.histological_structure,
    cpc.cell_phenotype
;

CREATE VIEW criterion_count AS
SELECT
    cpc.cell_phenotype as cell_phenotype_identifier,
    COUNT(*) as number_all_criteria
FROM
    cell_phenotype_criterion cpc
GROUP BY
    cpc.cell_phenotype
;

CREATE VIEW all_criteria_satisfied AS
SELECT
    cs.histological_structure as histological_structure,
    cc.cell_phenotype_identifier as cell_phenotype_identifier
FROM
    cells_count_criteria_satisfied cs
    JOIN criterion_count cc ON
        cs.number_criteria_satisfied = cc.number_all_criteria
    AND
        cs.cell_phenotype_identifier = cc.cell_phenotype_identifier
;

CREATE MATERIALIZED VIEW composite_marker_positive_cell_count_by_study_specimen AS
SELECT
    sdmp.study as study,
    sdmp.specimen as specimen,
    'composite' as multiplicity,
    cp.symbol as marker_symbol,
    COUNT(*) as cell_count
FROM
    all_criteria_satisfied s
    JOIN histological_structure_identification hsi ON
        s.histological_structure = hsi.histological_structure
    JOIN data_file df ON 
        hsi.data_source = df.sha256_hash
    JOIN specimen_data_measurement_process sdmp ON
        df.source_generation_process = sdmp.identifier
    JOIN cell_phenotype cp ON
        s.cell_phenotype_identifier = cp.identifier
GROUP BY
    sdmp.study,
    sdmp.specimen,
    cp.symbol
;

-- Aggregations
CREATE VIEW generalized_marker_positive_cell_count_by_study_specimen AS
SELECT * FROM marker_positive_cell_count_by_study_specimen
UNION
SELECT * FROM composite_marker_positive_cell_count_by_study_specimen
;

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

CREATE VIEW fraction_by_marker_study_specimen AS
SELECT
    cc.study as study,
    cc.specimen as specimen,
    pcc.multiplicity as multiplicity,
    pcc.marker_symbol as marker_symbol,
    100 * pcc.cell_count / CAST(cc.cell_count AS FLOAT) as percent_positive
FROM
    cell_count_by_study_specimen cc
    JOIN generalized_marker_positive_cell_count_by_study_specimen pcc
    ON
        cc.study = pcc.study
        AND
        cc.specimen = pcc.specimen
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
