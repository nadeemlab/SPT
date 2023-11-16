
ALTER TABLE diagnosis
ADD UNIQUE (subject, condition, result, assessor, date) ;

ALTER TABLE histology_assessment_process
ADD UNIQUE (slide, assay, result, assessor, assessment_date) ;

ALTER TABLE cell_phenotype_criterion
ADD UNIQUE (cell_phenotype, marker, polarity, study) ;

ALTER TABLE feature_specifier
ADD UNIQUE (feature_specification, specifier, ordinality) ;

ALTER TABLE two_cohort_feature_association_test
ADD UNIQUE (selection_criterion_1, selection_criterion_2, test, p_value, feature_tested) ;

ALTER TABLE expression_quantification
ADD range_identifier_integer SERIAL ;

CREATE TABLE range_definitions (
    scope_identifier VARCHAR(512),
    tablename VARCHAR(512),
    lowest_value INT,
    highest_value INT
) ;

CREATE EXTENSION IF NOT EXISTS tablefunc;

CREATE TABLE sample_strata (
    stratum_identifier VARCHAR(512),
    sample VARCHAR(512),
    local_temporal_position_indicator VARCHAR(512),
    subject_diagnosed_condition VARCHAR(512),
    subject_diagnosed_result VARCHAR(512)
);

CREATE TABLE umap_plots (
    study VARCHAR(512),
    channel VARCHAR(512),
    png_base64 VARCHAR
);

CREATE TABLE pending_feature_computation (
    feature_specification VARCHAR(512) REFERENCES feature_specification(identifier),
    time_initiated VARCHAR(512)
);
