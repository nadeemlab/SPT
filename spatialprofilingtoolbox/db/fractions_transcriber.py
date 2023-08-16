"""Make the phenotype fractions values available as general features."""

from pandas import read_sql
from numpy import isnan

from spatialprofilingtoolbox import DatabaseConnectionMaker
from spatialprofilingtoolbox.db.create_data_analysis_study import DataAnalysisStudyFactory
from spatialprofilingtoolbox.workflow.common.export_features import ADIFeaturesUploader
from spatialprofilingtoolbox import get_feature_description
from spatialprofilingtoolbox.workflow.common.two_cohort_feature_association_testing import \
    perform_tests
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


def transcribe_fraction_features(database_connection_maker: DatabaseConnectionMaker) -> None:
    connection = database_connection_maker.get_connection()
    feature_extraction_query = """
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
    fraction_features = read_sql(feature_extraction_query, connection)
    for study in fraction_features['study'].unique():
        fraction_features_study = fraction_features[fraction_features.study == study]
        das = DataAnalysisStudyFactory(connection, study, 'phenotype fractions').create()
        with ADIFeaturesUploader(
            database_connection_maker,
            data_analysis_study=das,
            derivation_and_number_specifiers=(
                get_feature_description('population fractions'), 1),
            impute_zeros=True,
        ) as feature_uploader:
            values = fraction_features_study['percent_positive'].values
            subjects = fraction_features_study['sample']
            specifiers = fraction_features_study['marker_symbol'].values
            for value, subject, specifier in zip(values, subjects, specifiers):
                if value is None or isnan(value):
                    continue
                feature_uploader.stage_feature_value((specifier,), subject, value / 100)
        perform_tests(das, connection)
