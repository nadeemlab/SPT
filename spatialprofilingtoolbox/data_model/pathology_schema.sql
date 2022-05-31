
-- Pathology ADI v0.6.0
CREATE TABLE IF NOT EXISTS subject (
    identifier VARCHAR(512) PRIMARY KEY,
    species VARCHAR(512),
    sex VARCHAR(512),
    birth_date VARCHAR,
    death_date VARCHAR,
    cause_of_death VARCHAR
);

CREATE TABLE IF NOT EXISTS diagnosis (
    subject VARCHAR(512) REFERENCES subject(identifier),
    condition VARCHAR,
    result VARCHAR(512),
    assessor VARCHAR(512),
    date VARCHAR
);

CREATE TABLE IF NOT EXISTS diagnostic_selection_criterion (
    identifier VARCHAR(512) PRIMARY KEY,
    condition VARCHAR(512),
    result VARCHAR(512)
);

CREATE TABLE IF NOT EXISTS specimen_collection_study (
    name VARCHAR(512) PRIMARY KEY,
    extraction_method VARCHAR(512),
    preservation_method VARCHAR(512),
    storage_location VARCHAR,
    inception_date VARCHAR,
    conclusion_date VARCHAR
);

CREATE TABLE IF NOT EXISTS specimen_collection_process (
    specimen VARCHAR PRIMARY KEY,
    source VARCHAR,
    source_site VARCHAR,
    source_age VARCHAR,
    extraction_date VARCHAR(512),
    study VARCHAR(512) REFERENCES specimen_collection_study(name)
);

CREATE TABLE IF NOT EXISTS histology_assessment_process (
    slide VARCHAR(512) REFERENCES specimen_collection_process(specimen),
    assay VARCHAR(512),
    result VARCHAR(512),
    assessor VARCHAR,
    assessment_date VARCHAR(512)
);

CREATE TABLE IF NOT EXISTS specimen_measurement_study (
    name VARCHAR(512) PRIMARY KEY,
    assay VARCHAR(512),
    machine VARCHAR(512),
    software VARCHAR(512),
    inception_date VARCHAR,
    conclusion_date VARCHAR
);

CREATE TABLE IF NOT EXISTS specimen_data_measurement_process (
    identifier VARCHAR(512) PRIMARY KEY,
    specimen VARCHAR(512) REFERENCES specimen_collection_process(specimen),
    specimen_age VARCHAR,
    date_of_measurement VARCHAR(512),
    study VARCHAR(512) REFERENCES specimen_measurement_study(name)
);

CREATE TABLE IF NOT EXISTS data_file (
    sha256_hash VARCHAR(512) PRIMARY KEY,
    file_name VARCHAR(512),
    file_format VARCHAR(512),
    contents_format VARCHAR(512),
    size VARCHAR(512),
    source_generation_process VARCHAR(512) REFERENCES specimen_data_measurement_process(identifier)
);

CREATE TABLE IF NOT EXISTS histological_structure (
    identifier VARCHAR(512) PRIMARY KEY,
    anatomical_entity VARCHAR(512)
);

CREATE TABLE IF NOT EXISTS shape_file (
    identifier VARCHAR(512) PRIMARY KEY,
    geometry_specification_file_format VARCHAR(512),
    base64_contents VARCHAR
);

CREATE TABLE IF NOT EXISTS plane_coordinates_reference_system (
    name VARCHAR(512) PRIMARY KEY,
    reference_point VARCHAR,
    reference_point_coordinate_1 NUMERIC,
    reference_point_coordinate_2 NUMERIC,
    reference_orientation VARCHAR,
    length_unit VARCHAR
);

CREATE TABLE IF NOT EXISTS histological_structure_identification (
    histological_structure VARCHAR(512) REFERENCES histological_structure(identifier),
    data_source VARCHAR(512) REFERENCES data_file(sha256_hash),
    shape_file VARCHAR(512) REFERENCES shape_file(identifier),
    plane_coordinates_reference VARCHAR(512) REFERENCES plane_coordinates_reference_system(name),
    identification_method VARCHAR(512),
    identification_date VARCHAR(512),
    annotator VARCHAR
);

CREATE TABLE IF NOT EXISTS chemical_species (
    identifier VARCHAR(512) PRIMARY KEY,
    symbol VARCHAR,
    name VARCHAR(512),
    chemical_structure_class VARCHAR(512)
);

CREATE TABLE IF NOT EXISTS expression_quantification (
    histological_structure VARCHAR(512) REFERENCES histological_structure(identifier),
    target VARCHAR(512) REFERENCES chemical_species(identifier),
    quantity NUMERIC,
    unit VARCHAR(512),
    quantification_method VARCHAR(512),
    discrete_value VARCHAR(512),
    discretization_method VARCHAR(512)
);

CREATE TABLE IF NOT EXISTS biological_marking_system (
    identifier VARCHAR(512) PRIMARY KEY,
    target VARCHAR(512) REFERENCES chemical_species(identifier),
    antibody VARCHAR,
    marking_mechanism VARCHAR(512),
    study VARCHAR(512) REFERENCES specimen_measurement_study(name)
);

CREATE TABLE IF NOT EXISTS data_analysis_study (
    name VARCHAR(512) PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS cell_phenotype (
    identifier VARCHAR(512) PRIMARY KEY,
    symbol VARCHAR,
    name VARCHAR(512)
);

CREATE TABLE IF NOT EXISTS cell_phenotype_criterion (
    cell_phenotype VARCHAR(512) REFERENCES cell_phenotype(identifier),
    marker VARCHAR(512) REFERENCES chemical_species(identifier),
    polarity VARCHAR(512),
    study VARCHAR(512) REFERENCES data_analysis_study(name)
);

CREATE TABLE IF NOT EXISTS feature_specification (
    identifier VARCHAR(512) PRIMARY KEY,
    derivation_method VARCHAR(512),
    study VARCHAR(512) REFERENCES data_analysis_study(name)
);

CREATE TABLE IF NOT EXISTS feature_specifier (
    feature_specification VARCHAR(512) REFERENCES feature_specification(identifier),
    specifier VARCHAR(512),
    ordinality VARCHAR(512)
);

CREATE TABLE IF NOT EXISTS quantitative_feature_value (
    identifier VARCHAR(512) PRIMARY KEY,
    feature VARCHAR(512) REFERENCES feature_specification(identifier),
    subject VARCHAR,
    value NUMERIC
);

CREATE TABLE IF NOT EXISTS two_cohort_feature_association_test (
    selection_criterion_1 VARCHAR(512) REFERENCES diagnostic_selection_criterion(identifier),
    selection_criterion_2 VARCHAR(512) REFERENCES diagnostic_selection_criterion(identifier),
    test VARCHAR(512),
    p_value NUMERIC,
    feature_tested VARCHAR(512) REFERENCES feature_specification(identifier)
);
