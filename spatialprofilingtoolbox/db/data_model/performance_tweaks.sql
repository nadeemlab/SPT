
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

CREATE EXTENSION IF NOT EXISTS tablefunc;

CREATE TABLE sample_stratification (
    sample VARCHAR(512),
    temporal_position_relative_to_interventions VARCHAR(512),
    diagnosis VARCHAR(512)
);
