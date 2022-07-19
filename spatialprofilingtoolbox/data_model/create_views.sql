
-- Single phenotype counts
CREATE MATERIALIZED VIEW marker_positive_cell_count_by_study_specimen AS
SELECT
    sdmp.study as measurement_study,
    'none' as data_analysis_study,
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
    cpc.study as data_analysis_study,
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
    cpc.study,
    eq.histological_structure,
    cpc.cell_phenotype
;

CREATE VIEW criterion_count AS
SELECT
    cpc.study as data_analysis_study,
    cpc.cell_phenotype as cell_phenotype_identifier,
    COUNT(*) as number_all_criteria
FROM
    cell_phenotype_criterion cpc
GROUP BY
    cpc.study,
    cpc.cell_phenotype
;

CREATE VIEW all_criteria_satisfied AS
SELECT
    cs.data_analysis_study as data_analysis_study,
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
    sdmp.study as measurement_study,
    s.data_analysis_study as data_analysis_study,
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
    s.data_analysis_study,
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
    sdmp.study as measurement_study,
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
    cc.measurement_study as measurement_study,
    pcc.data_analysis_study as data_analysis_study,
    cc.specimen as specimen,
    pcc.multiplicity as multiplicity,
    pcc.marker_symbol as marker_symbol,
    100 * pcc.cell_count / CAST(cc.cell_count AS FLOAT) as percent_positive
FROM
    cell_count_by_study_specimen cc
    JOIN generalized_marker_positive_cell_count_by_study_specimen pcc
    ON
        cc.measurement_study = pcc.measurement_study
        AND
        cc.specimen = pcc.specimen
;

CREATE VIEW fraction_generalized_cases AS
SELECT *
FROM
    (
    SELECT
        f.measurement_study as measurement_study,
        f.data_analysis_study as data_analysis_study,
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
        g.measurement_study as measurement_study,
        g.data_analysis_study as data_analysis_study,
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
    measurement_study, data_analysis_study, multiplicity, marker_symbol, assay, assessment, specimen
;

-- Summary stats
-- (mean, standard deviation)
CREATE VIEW fraction_moments_generalized_cases AS
SELECT
    measurement_study, data_analysis_study, marker_symbol, multiplicity, assay, assessment,
    CAST(AVG(f.percent_positive) AS NUMERIC(5, 2)) as average_percent,
    CAST(STDDEV(f.percent_positive) AS NUMERIC(5, 2)) as standard_deviation_of_percents
FROM
    fraction_generalized_cases f
GROUP BY
    measurement_study, data_analysis_study, multiplicity, marker_symbol, assay, assessment
ORDER BY
    measurement_study, data_analysis_study, multiplicity, marker_symbol, assay, assessment
;

-- (extrema)
CREATE VIEW fraction_extrema AS
SELECT
    measurement_study, data_analysis_study, marker_symbol, multiplicity, assay, assessment,
    MAX(f.percent_positive) as maximum_percent,
    MIN(f.percent_positive) as minimum_percent
FROM fraction_generalized_cases f
GROUP BY
    measurement_study, data_analysis_study, marker_symbol, multiplicity, assay, assessment
;

CREATE VIEW fraction_arg_maxima AS
SELECT
    measurement_study, data_analysis_study, marker_symbol, multiplicity, assay, assessment,
    MIN(possibly_with_multiples.specimen) as specimen,
    MIN(possibly_with_multiples.maximum_percent) as maximum_percent
FROM
    (
    SELECT
        f.measurement_study as measurement_study, f.data_analysis_study as data_analysis_study, f.marker_symbol as marker_symbol, f.multiplicity as multiplicity, f.assay as assay, f.assessment as assessment,
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
    measurement_study, data_analysis_study, multiplicity, marker_symbol, assay, assessment
ORDER BY
    measurement_study, data_analysis_study, multiplicity, marker_symbol, assay, assessment
;

CREATE VIEW fraction_arg_minima AS
SELECT
    measurement_study, data_analysis_study, marker_symbol, multiplicity, assay, assessment,
    MIN(possibly_with_multiples.specimen) as specimen,
    MIN(possibly_with_multiples.minimum_percent) as minimum_percent
FROM
    (
    SELECT
        f.measurement_study as measurement_study, f.data_analysis_study as data_analysis_study, f.marker_symbol as marker_symbol, f.multiplicity as multiplicity, f.assay as assay, f.assessment as assessment,
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
    measurement_study, data_analysis_study, multiplicity, marker_symbol, assay, assessment
ORDER BY
    measurement_study, data_analysis_study, multiplicity, marker_symbol, assay, assessment
;

-- (stats)
CREATE MATERIALIZED VIEW fraction_stats AS
SELECT
    f1.measurement_study, f1.data_analysis_study, f1.marker_symbol, f1.multiplicity, f1.assay, f1.assessment,
    f3.average_percent,
    f3.standard_deviation_of_percents,
    f1.specimen as maximum,
    CAST(f1.maximum_percent AS NUMERIC(5, 2)) as maximum_value,
    f2.specimen as minimum,
    CAST(f2.minimum_percent AS NUMERIC(5, 2)) as minimum_value
FROM
    fraction_arg_maxima f1
    JOIN fraction_arg_minima f2 ON
        f1.measurement_study = f2.measurement_study
    AND
        f1.data_analysis_study = f2.data_analysis_study
    AND
        f1.multiplicity = f2.multiplicity
    AND
        f1.marker_symbol = f2.marker_symbol
    AND
        f1.assay = f2.assay
    AND
        f1.assessment = f2.assessment
    JOIN fraction_moments_generalized_cases f3 ON
        f1.measurement_study = f3.measurement_study
    AND
        f1.data_analysis_study = f3.data_analysis_study
    AND
        f1.multiplicity = f3.multiplicity
    AND
        f1.marker_symbol = f3.marker_symbol
    AND
        f1.assay = f3.assay
    AND
        f1.assessment = f3.assessment
ORDER BY
    measurement_study, data_analysis_study, multiplicity DESC, marker_symbol, assay, assessment
;

-- computed features
CREATE VIEW features_3_specifiers AS
SELECT
    qfv.subject as subject,
    qfv.value as value,
    "1" as specifier1,
    "2" as specifier2,
    "3" as specifier3,
    fsn.derivation_method as derivation_method,
    fsn.study as study
FROM
    crosstab('select feature_specification, ordinality, specifier from feature_specifier order by 1,2')
    AS
    ct(feature_specification varchar(512), "1" varchar(512), "2" varchar(512), "3" varchar(512))
    JOIN feature_specification fsn ON
        fsn.identifier = ct.feature_specification
    JOIN quantitative_feature_value qfv ON
        qfv.feature = ct.feature_specification    
;


CREATE VIEW features_3_specifiers_maxima AS
SELECT
    DISTINCT ON(sq.maximum_value, f3s.specifier1, f3s.specifier2, f3s.specifier3, f3s.derivation_method, f3s.study)
    f3s.subject as maximum, sq.maximum_value as maximum_value, f3s.specifier1, f3s.specifier2, f3s.specifier3, f3s.derivation_method, f3s.study
FROM
    features_3_specifiers f3s
JOIN
    (
    SELECT
        MAX(f3s.value) as maximum_value, f3s.specifier1, f3s.specifier2, f3s.specifier3, f3s.derivation_method, f3s.study
    FROM
        features_3_specifiers f3s
    GROUP BY
        specifier1, specifier2, specifier3, derivation_method, study
    ) as sq
    ON
        sq.specifier1 = f3s.specifier1 AND sq.specifier2 = f3s.specifier2 AND sq.specifier3 = f3s.specifier3 AND sq.derivation_method = f3s.derivation_method AND sq.study = f3s.study
    AND
        sq.maximum_value = f3s.value
;

CREATE VIEW features_3_specifiers_minima AS
SELECT
    DISTINCT ON(sq.minimum_value, f3s.specifier1, f3s.specifier2, f3s.specifier3, f3s.derivation_method, f3s.study)
    f3s.subject as minimum, sq.minimum_value as minimum_value, f3s.specifier1, f3s.specifier2, f3s.specifier3, f3s.derivation_method, f3s.study
FROM
    features_3_specifiers f3s
JOIN
    (
    SELECT
        MIN(f3s.value) as minimum_value, f3s.specifier1, f3s.specifier2, f3s.specifier3, f3s.derivation_method, f3s.study
    FROM
        features_3_specifiers f3s
    GROUP BY
        specifier1, specifier2, specifier3, derivation_method, study
    ) as sq
    ON
        sq.specifier1 = f3s.specifier1 AND sq.specifier2 = f3s.specifier2 AND sq.specifier3 = f3s.specifier3 AND sq.derivation_method = f3s.derivation_method AND sq.study = f3s.study
    AND
        sq.minimum_value = f3s.value
;

CREATE VIEW features_3_specifiers_mean AS
SELECT
    AVG(f3s.value) as mean,
    f3s.specifier1, f3s.specifier2, f3s.specifier3, f3s.derivation_method, f3s.study
FROM
    features_3_specifiers f3s
GROUP BY
    f3s.specifier1, f3s.specifier2, f3s.specifier3, f3s.derivation_method, f3s.study
;

-- Needs assay, assessment, and standard deviation
CREATE VIEW features_3_specifiers_stats AS
SELECT
    f_mean.mean as mean,
    f_min.minimum_value as minimum_value,
    f_min.minimum as minimum,
    f_max.maximum_value as maximum_value,
    f_max.maximum as maximum,
    f_mean.specifier1, f_mean.specifier2, f_mean.specifier3, f_mean.derivation_method, f_mean.study
FROM
    features_3_specifiers_mean f_mean
JOIN
    features_3_specifiers_minima f_min
ON
    f_min.specifier1 = f_mean.specifier1 AND f_min.specifier2 = f_mean.specifier2 AND f_min.specifier3 = f_mean.specifier3 AND f_min.derivation_method = f_mean.derivation_method AND f_min.study = f_mean.study
JOIN
    features_3_specifiers_maxima f_max
ON
    f_max.specifier1 = f_mean.specifier1 AND f_max.specifier2 = f_mean.specifier2 AND f_max.specifier3 = f_mean.specifier3 AND f_max.derivation_method = f_mean.derivation_method AND f_max.study = f_mean.study
ORDER BY
    mean DESC, f_mean.specifier1, f_mean.specifier2, f_mean.specifier3, f_mean.derivation_method, f_mean.study
;
