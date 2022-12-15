
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

-- (build cases sets)
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
        NULL as stratum_identifier,
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
        sst.stratum_identifier as stratum_identifier,
        g.specimen as specimen,
        g.percent_positive as percent_positive
    FROM
        fraction_by_marker_study_specimen g
        JOIN sample_strata sst ON
            g.specimen = sst.sample
    )
ORDER BY
    measurement_study, data_analysis_study, multiplicity, marker_symbol, stratum_identifier, specimen
;

-- Summary stats
-- (mean, standard deviation)
CREATE VIEW fraction_moments_generalized_cases AS
SELECT
    measurement_study, data_analysis_study, marker_symbol, multiplicity, stratum_identifier,
    CAST(AVG(f.percent_positive) AS NUMERIC(5, 2)) as average_percent,
    CAST(STDDEV(f.percent_positive) AS NUMERIC(5, 2)) as standard_deviation_of_percents
FROM
    fraction_generalized_cases f
GROUP BY
    measurement_study, data_analysis_study, multiplicity, marker_symbol, stratum_identifier
ORDER BY
    measurement_study, data_analysis_study, multiplicity, marker_symbol, stratum_identifier
;

-- (extrema)
CREATE VIEW fraction_extrema AS
SELECT
    measurement_study, data_analysis_study, marker_symbol, multiplicity, stratum_identifier,
    MAX(f.percent_positive) as maximum_percent,
    MIN(f.percent_positive) as minimum_percent
FROM fraction_generalized_cases f
GROUP BY
    measurement_study, data_analysis_study, marker_symbol, multiplicity, stratum_identifier
;

CREATE VIEW fraction_arg_maxima AS
SELECT
    measurement_study, data_analysis_study, marker_symbol, multiplicity, stratum_identifier,
    MIN(possibly_with_multiples.specimen) as specimen,
    MIN(possibly_with_multiples.maximum_percent) as maximum_percent
FROM
    (
    SELECT
        f.measurement_study as measurement_study, f.data_analysis_study as data_analysis_study, f.marker_symbol as marker_symbol, f.multiplicity as multiplicity, f.stratum_identifier as stratum_identifier,
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
    measurement_study, data_analysis_study, multiplicity, marker_symbol, stratum_identifier
ORDER BY
    measurement_study, data_analysis_study, multiplicity, marker_symbol, stratum_identifier
;

CREATE VIEW fraction_arg_minima AS
SELECT
    measurement_study, data_analysis_study, marker_symbol, multiplicity, stratum_identifier,
    MIN(possibly_with_multiples.specimen) as specimen,
    MIN(possibly_with_multiples.minimum_percent) as minimum_percent
FROM
    (
    SELECT
        f.measurement_study as measurement_study, f.data_analysis_study as data_analysis_study, f.marker_symbol as marker_symbol, f.multiplicity as multiplicity, f.stratum_identifier as stratum_identifier,
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
    measurement_study, data_analysis_study, multiplicity, marker_symbol, stratum_identifier
ORDER BY
    measurement_study, data_analysis_study, multiplicity, marker_symbol, stratum_identifier
;

-- (stats)
CREATE MATERIALIZED VIEW fraction_stats AS
SELECT
    f1.measurement_study, f1.data_analysis_study, f1.marker_symbol, f1.multiplicity, f1.stratum_identifier,
    f3.average_percent,
    f3.standard_deviation_of_percents,
    f1.specimen as maximum,
    CAST(f1.maximum_percent AS NUMERIC(5, 2)) as maximum_value,
    f2.specimen as minimum,
    CAST(f2.minimum_percent AS NUMERIC(5, 2)) as minimum_value
FROM
    fraction_arg_maxima f1
    JOIN fraction_arg_minima f2 ON
        f1.measurement_study = f2.measurement_study AND f1.data_analysis_study = f2.data_analysis_study AND f1.multiplicity = f2.multiplicity AND f1.marker_symbol = f2.marker_symbol AND f1.stratum_identifier = f2.stratum_identifier
    JOIN fraction_moments_generalized_cases f3 ON
        f1.measurement_study = f3.measurement_study AND f1.data_analysis_study = f3.data_analysis_study AND f1.multiplicity = f3.multiplicity AND f1.marker_symbol = f3.marker_symbol AND f1.stratum_identifier = f3.stratum_identifier
ORDER BY
    measurement_study, data_analysis_study, multiplicity DESC, marker_symbol, stratum_identifier
;

-- Computed features
-- (build cases sets)
CREATE MATERIALIZED VIEW computed_feature_3_specifiers_study_specimen AS
SELECT
    fsn.study as data_analysis_study,
    fsn.derivation_method as derivation_method,
    "1" as specifier1,
    "2" as specifier2,
    "3" as specifier3,
    qfv.subject as specimen,
    qfv.value as computed_value
FROM
    crosstab('select feature_specification, ordinality, specifier from feature_specifier order by 1,2')
    AS
    ct(feature_specification varchar(512), "1" varchar(512), "2" varchar(512), "3" varchar(512))
    JOIN feature_specification fsn ON
        fsn.identifier = ct.feature_specification
    JOIN quantitative_feature_value qfv ON
        qfv.feature = ct.feature_specification    
;

CREATE MATERIALIZED VIEW computed_feature_3_specifiers_generalized_cases AS
SELECT *
FROM
    (
    SELECT
        f.data_analysis_study as data_analysis_study,
        f.derivation_method as derivation_method,
        f.specifier1 as specifier1,
        f.specifier2 as specifier2,
        f.specifier3 as specifier3,
        NULL as stratum_identifier,
        f.specimen as specimen,
        f.computed_value as computed_value
    FROM
        computed_feature_3_specifiers_study_specimen f
    ) no_specific_assessment
    UNION
    (
    SELECT
        g.data_analysis_study as data_analysis_study,
        g.derivation_method as derivation_method,
        g.specifier1 as specifier1,
        g.specifier2 as specifier2,
        g.specifier3 as specifier3,
        sst.stratum_identifier as stratum_identifier,
        g.specimen as specimen,
        g.computed_value as computed_value
    FROM
        computed_feature_3_specifiers_study_specimen g
        JOIN sample_strata sst ON
            g.specimen = sst.sample
    )
ORDER BY
    data_analysis_study, specifier1, specifier2, specifier3, stratum_identifier
;

-- (mean, standard deviation)
CREATE MATERIALIZED VIEW computed_feature_3_specifiers_moments_generalized_cases AS
SELECT
    data_analysis_study, derivation_method, specifier1, specifier2, specifier3, stratum_identifier,
    CAST(AVG(cf.computed_value) AS NUMERIC(5, 2)) as average_value,
    CAST(STDDEV(cf.computed_value) AS NUMERIC(5, 2)) as standard_deviation
FROM
    computed_feature_3_specifiers_generalized_cases cf
GROUP BY
    data_analysis_study, derivation_method, specifier1, specifier2, specifier3, stratum_identifier
ORDER BY
    data_analysis_study, derivation_method, specifier1, specifier2, specifier3, stratum_identifier
;

-- (extrema)
CREATE MATERIALIZED VIEW computed_feature_3_specifiers_maxima AS
SELECT
    DISTINCT ON(sq.maximum_value, cf.specifier1, cf.specifier2, cf.specifier3, cf.derivation_method, cf.data_analysis_study, cf.stratum_identifier)
    cf.specimen as maximum, sq.maximum_value as maximum_value, cf.specifier1, cf.specifier2, cf.specifier3, cf.derivation_method, cf.data_analysis_study, cf.stratum_identifier
FROM
    computed_feature_3_specifiers_generalized_cases cf
JOIN
    (
    SELECT
        MAX(cfs.computed_value) as maximum_value, cfs.specifier1, cfs.specifier2, cfs.specifier3, cfs.derivation_method, cfs.data_analysis_study, cfs.stratum_identifier
    FROM
        computed_feature_3_specifiers_generalized_cases cfs
    GROUP BY
        specifier1, specifier2, specifier3, derivation_method, data_analysis_study, stratum_identifier
    ) as sq
    ON
        sq.specifier1 = cf.specifier1 AND sq.specifier2 = cf.specifier2 AND sq.specifier3 = cf.specifier3 AND sq.derivation_method = cf.derivation_method AND sq.data_analysis_study = cf.data_analysis_study AND sq.stratum_identifier = cf.stratum_identifier
    AND
        sq.maximum_value = cf.computed_value
;

CREATE MATERIALIZED VIEW computed_feature_3_specifiers_minima AS
SELECT
    DISTINCT ON(sq.minimum_value, cf.specifier1, cf.specifier2, cf.specifier3, cf.derivation_method, cf.data_analysis_study, cf.stratum_identifier)
    cf.specimen as minimum, sq.minimum_value as minimum_value, cf.specifier1, cf.specifier2, cf.specifier3, cf.derivation_method, cf.data_analysis_study, cf.stratum_identifier
FROM
    computed_feature_3_specifiers_generalized_cases cf
JOIN
    (
    SELECT
        MIN(cfs.computed_value) as minimum_value, cfs.specifier1, cfs.specifier2, cfs.specifier3, cfs.derivation_method, cfs.data_analysis_study, cfs.stratum_identifier
    FROM
        computed_feature_3_specifiers_generalized_cases cfs
    GROUP BY
        specifier1, specifier2, specifier3, derivation_method, data_analysis_study, stratum_identifier
    ) as sq
    ON
        sq.specifier1 = cf.specifier1 AND sq.specifier2 = cf.specifier2 AND sq.specifier3 = cf.specifier3 AND sq.derivation_method = cf.derivation_method AND sq.data_analysis_study = cf.data_analysis_study AND sq.stratum_identifier = cf.stratum_identifier
    AND
        sq.minimum_value = cf.computed_value
;

-- (stats)
CREATE MATERIALIZED VIEW computed_feature_3_specifiers_stats AS
SELECT
    f1.data_analysis_study, f1.derivation_method, f1.specifier1, f1.specifier2, f1.specifier3, f1.stratum_identifier,
    f3.average_value,
    f3.standard_deviation,
    f1.maximum as maximum,
    CAST(f1.maximum_value AS NUMERIC(5, 2)) as maximum_value,
    f2.minimum as minimum,
    CAST(f2.minimum_value AS NUMERIC(5, 2)) as minimum_value
FROM
    computed_feature_3_specifiers_maxima f1
    JOIN computed_feature_3_specifiers_minima f2 ON
        f1.data_analysis_study = f2.data_analysis_study AND f1.derivation_method = f2.derivation_method AND f1.specifier1 = f2.specifier1 AND f1.specifier2 = f2.specifier2 AND f1.specifier3 = f2.specifier3 AND f1.stratum_identifier = f2.stratum_identifier
    JOIN computed_feature_3_specifiers_moments_generalized_cases f3 ON
        f1.data_analysis_study = f3.data_analysis_study AND f1.derivation_method = f3.derivation_method AND f1.specifier1 = f3.specifier1 AND f1.specifier2 = f3.specifier2 AND f1.specifier3 = f3.specifier3 AND f1.stratum_identifier = f3.stratum_identifier
ORDER BY
    data_analysis_study, derivation_method, specifier1, specifier2, specifier3, stratum_identifier
;
