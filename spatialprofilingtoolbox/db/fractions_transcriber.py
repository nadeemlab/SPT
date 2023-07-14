"""Make the phenotype fractions values available as general features."""
import datetime
import re

import pandas as pd

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.workflow.common.export_features import ADIFeaturesUploader
from spatialprofilingtoolbox.workflow.common.two_cohort_feature_association_testing import \
    perform_tests
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


def describe_fractions_feature_derivation_method():
    return '''
    For a given cell phenotype, the average number of cells of that phenotype in the given sample relative to the number of cells in the sample.
    '''.lstrip().rstrip()


def insert_new_data_analysis_study(database_connection_maker, study_name, specifier):
    timestring = str(datetime.datetime.now())
    name = f'{study_name} : {specifier} : {timestring}'
    connection = database_connection_maker.get_connection()
    cursor = connection.cursor()
    cursor.execute('''
    INSERT INTO data_analysis_study(name)
    VALUES (%s) ;
    INSERT INTO study_component(primary_study, component_study)
    VALUES (%s, %s) ;
    ''', (name, study_name, name))
    cursor.close()
    connection.commit()
    logger.info('Inserted data analysis study: "%s"', name)
    return name


def fractions_study_exists(database_connection_maker, study):
    connection = database_connection_maker.get_connection()
    cursor = connection.cursor()
    cursor.execute('''
    SELECT das.name
    FROM data_analysis_study das
    JOIN study_component sc ON sc.component_study=das.name
    WHERE sc.primary_study=%s
    ;
    ''', (study,))
    names = [row[0] for row in cursor.fetchall()]
    if any(re.search('phenotype fractions', name) for name in names):
        return True
    return False


def create_fractions_study(database_connection_maker, study):
    das = insert_new_data_analysis_study(database_connection_maker, study, 'phenotype fractions')
    return das


def transcribe_fraction_features(database_connection_maker: DatabaseConnectionMaker):
    """
    Transcribe phenotype fraction features in features system.
    """
    connection = database_connection_maker.get_connection()
    feature_extraction_query="""
    SELECT
        sc.primary_study as study,
        f.specimen as sample,
        f.marker_symbol,
        f.percent_positive
    FROM fraction_by_marker_study_specimen f
    JOIN study_component sc ON sc.component_study=f.measurement_study
    ORDER BY
        sc.primary_study,
        f.data_analysis_study,
        f.specimen
    ;
    """
    fraction_features = pd.read_sql(feature_extraction_query, connection)

    for study in fraction_features['study'].unique():
        fraction_features_study = fraction_features[fraction_features.study == study]
        if fractions_study_exists(database_connection_maker, study):
            logger.debug('Fractions study already exists for %s.', study)
            continue
        das = create_fractions_study(database_connection_maker, study)
        with ADIFeaturesUploader(
            database_connection_maker,
            data_analysis_study=das,
            derivation_and_number_specifiers = (describe_fractions_feature_derivation_method(), 1),
            impute_zeros=True,
        ) as feature_uploader:
            values = fraction_features_study['percent_positive'].values
            subjects = fraction_features_study['sample']
            specifiers = fraction_features_study['marker_symbol'].values
            for value, subject, specifier in zip(values, subjects, specifiers):
                feature_uploader.stage_feature_value((specifier,), subject, value / 100)

        perform_tests(das, connection)
