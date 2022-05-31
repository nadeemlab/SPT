
ALTER TABLE diagnosis
ADD CONSTRAINT  
UNIQUE (subject, condition, result, assessor, date) ;

ALTER TABLE histology_assessment_process
ADD CONSTRAINT
UNIQUE (slide, assay, result, assessor, assessment_date) ;

ALTER TABLE cell_phenotype_criterion
ADD CONSTRAINT
UNIQUE (cell_phenotype, marker, polarity, study) ;

ALTER TABLE feature_specifier
ADD CONSTRAINT
UNIQUE (feature_specification, specifier, ordinality) ;

ALTER TABLE two_cohort_feature_association_test
ADD CONSTRAINT
UNIQUE (selection_criterion_1, selection_criterion_2, test, p_value, feature_tested) ;
