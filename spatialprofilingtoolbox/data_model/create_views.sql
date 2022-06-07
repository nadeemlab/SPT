
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

CREATE VIEW fraction_generalized_cases AS
SELECT *
FROM
    (
    SELECT
        f.study as study,
        f.marker_symbol as marker_symbol,
        f.multiplicity as multiplicity,
        '<any>' as assay,
        '<any>' as assessment,
        f.specimen as specimen,
        f.percent_positive as percent_positive
    FROM
        fraction_by_marker_study_specimen f
    ) no_specific_assessment
    UNION
    (
    SELECT
        g.study as study,
        g.marker_symbol as marker_symbol,
        g.multiplicity as multiplicity,
        hap.assay as assay,
        hap.result as assessment,
        g.specimen as specimen,
        g.percent_positive as percent_positive
    FROM
        fraction_by_marker_study_specimen g
        JOIN histology_assessment_process hap ON
            g.specimen = hap.slide
    )
ORDER BY
    study,
    multiplicity,
    marker_symbol,
    assay,
    assessment,
    specimen
;

-- Summary stats
-- (mean, standard deviation)
CREATE VIEW fraction_moments_generalized_cases AS
SELECT
    study, marker_symbol, multiplicity, assay, assessment,
    CAST(AVG(f.percent_positive) AS NUMERIC(7, 4)) as average_percent,
    CAST(STDDEV(f.percent_positive) AS NUMERIC(7, 4)) as standard_deviation_of_percents
FROM
    fraction_generalized_cases f
GROUP BY
    study, marker_symbol, multiplicity, assay, assessment
ORDER BY
    study, multiplicity, marker_symbol, assay, assessment
;

-- (extrema)
CREATE VIEW fraction_extrema AS
SELECT
    study, marker_symbol, multiplicity, assay, assessment,
    MAX(f.percent_positive) as maximum_percent,
    MIN(f.percent_positive) as minimum_percent
FROM fraction_generalized_cases f
GROUP BY
    study, marker_symbol, multiplicity, assay, assessment
;

CREATE VIEW fraction_arg_maxima AS
SELECT
    study, marker_symbol, multiplicity, assay, assessment,
    MIN(possibly_with_multiples.specimen) as specimen,
    MIN(possibly_with_multiples.maximum_percent) as maximum_percent
FROM
    (
    SELECT
        f.study as study, f.marker_symbol as marker_symbol, f.multiplicity as multiplicity, f.assay as assay, f.assessment as assessment,
        f.specimen as specimen,
        e.maximum_percent as maximum_percent
    FROM
        fraction_generalized_cases f
        JOIN fraction_extrema e ON
            f.percent_positive = e.maximum_percent
        AND
            f.marker_symbol = e.marker_symbol
    ) as possibly_with_multiples
GROUP BY
    study, multiplicity, marker_symbol, assay, assessment
ORDER BY
    study, multiplicity, marker_symbol, assay, assessment
;

CREATE VIEW fraction_arg_minima AS
SELECT
    study, marker_symbol, multiplicity, assay, assessment,
    MIN(possibly_with_multiples.specimen) as specimen,
    MIN(possibly_with_multiples.minimum_percent) as minimum_percent
FROM
    (
    SELECT
        f.study as study, f.marker_symbol as marker_symbol, f.multiplicity as multiplicity, f.assay as assay, f.assessment as assessment,
        f.specimen as specimen,
        e.minimum_percent as minimum_percent
    FROM
        fraction_generalized_cases f
        JOIN fraction_extrema e ON
            f.percent_positive = e.minimum_percent
        AND
            f.marker_symbol = e.marker_symbol
    ) as possibly_with_multiples
GROUP BY
    study, multiplicity, marker_symbol, assay, assessment
ORDER BY
    study, multiplicity, marker_symbol, assay, assessment
;

-- (stats)
CREATE MATERIALIZED VIEW fraction_stats AS
SELECT
    f1.study, f1.marker_symbol, f1.multiplicity, f1.assay, f1.assessment,
    f3.average_percent,
    f3.standard_deviation_of_percents,
    f1.specimen as maximum,
    CAST(f1.maximum_percent AS NUMERIC(7, 4)) as maximum_value,
    f2.specimen as minimum,
    CAST(f2.minimum_percent AS NUMERIC(7, 4)) as minimum_value
FROM
    fraction_arg_maxima f1
    JOIN fraction_arg_minima f2 ON
        f1.study = f2.study
    AND
        f1.multiplicity = f2.multiplicity
    AND
        f1.marker_symbol = f2.marker_symbol
    AND
        f1.assay = f2.assay
    AND
        f1.assessment = f2.assessment
    JOIN fraction_moments_generalized_cases f3 ON
        f1.study = f3.study
    AND
        f1.multiplicity = f3.multiplicity
    AND
        f1.marker_symbol = f3.marker_symbol
    AND
        f1.assay = f3.assay
    AND
        f1.assessment = f3.assessment
ORDER BY
    study, multiplicity DESC, marker_symbol, assay, assessment
;

