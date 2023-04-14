"""Make the phenotype fractions values available as general features."""

import datetime

import pandas as pd

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.workflow.common.export_features import ADIFeaturesUploader


def describe_fractions_feature_derivation_method():
    return '''
    For a given cell phenotype, the average number of cells of that phenotype in the given sample.
    '''.lstrip().rstrip()


def insert_new_data_analysis_study(database_config_file, study_name, specifier):
    timestring = str(datetime.datetime.now())
    name = study_name + f'{study_name} : {specifier} : {timestring}'
    with DatabaseConnectionMaker(database_config_file) as dcm:
        connection = dcm.get_connection()
        cursor = connection.cursor()
        cursor.execute('''
        INSERT INTO data_analysis_study(name)
        VALUES (%s) ;
        INSERT INTO study_component(primary_study, component_study)
        VALUES (%s, %s) ;
        ''', (name, study_name, name))
        cursor.close()
        connection.commit()
    return name


def transcribe_fraction_features(database_config_file):
    """
    Transcribe phenotype fraction features in features system.
    """
    with DatabaseConnectionMaker(database_config_file=database_config_file) as dcm:
        connection = dcm.get_connection()
        feature_extraction_query="""
            SELECT
                sc.primary_study as study,
                f.specimen as sample,
                f.marker_symbol,
                f.percent_positive,
                ss.stratum_identifier
            FROM fraction_by_marker_study_specimen f
            JOIN sample_strata ss ON ss.sample=f.specimen
            JOIN study_component sc ON sc.component_study=f.measurement_study
            ORDER BY
                sc.primary_study,
                f.data_analysis_study,
                ss.stratum_identifier,
                f.specimen
            ;
        """
        fraction_features = pd.read_sql(feature_extraction_query, connection)

    for study in fraction_features['study'].unique():
        fraction_features_study = fraction_features[fraction_features.study == study]
        das = insert_new_data_analysis_study(database_config_file, study, 'phenotype fractions')
        with ADIFeaturesUploader(
            database_config_file=database_config_file,
            data_analysis_study=das,
            derivation_method=describe_fractions_feature_derivation_method(),
            specifier_number=1,
        ) as feature_uploader:
            values = fraction_features_study['percent_positive'].values
            subjects = fraction_features_study['sample']
            specifiers = fraction_features_study['marker_symbol'].values
            for value, subject, specifier in zip(values, subjects, specifiers):
                feature_uploader.stage_feature_value((specifier,), subject, value)
