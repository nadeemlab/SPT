"""Make squidpy metrics that don't require specific phenotype selection available."""

from pandas import DataFrame
from psycopg2.extensions import cursor as Psycopg2Cursor

from spatialprofilingtoolbox import DatabaseConnectionMaker
from spatialprofilingtoolbox.db.feature_matrix_extractor import FeatureMatrixExtractor
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.db.create_data_analysis_study import DataAnalysisStudyFactory
from spatialprofilingtoolbox.workflow.common.squidpy import (
    compute_squidpy_metric_for_one_sample,
)
from spatialprofilingtoolbox.workflow.common.export_features import ADIFeaturesUploader
from spatialprofilingtoolbox import get_feature_description
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


def create_and_transcribe_squidpy_features(
    database_connection_maker: DatabaseConnectionMaker,
    study: str,
) -> None:
    """Transcribe "off-demand" Squidpy feature(s) in features system."""
    connection = database_connection_maker.get_connection()
    das = DataAnalysisStudyFactory(connection, study, 'spatial autocorrelation').create()
    features_by_specimen = _fetch_cells(connection.cursor(), study)
    with ADIFeaturesUploader(
        database_connection_maker,
        data_analysis_study=das,
        derivation_and_number_specifiers=(get_feature_description("spatial autocorrelation"), 1),
        impute_zeros=True,
        upload_anyway=True,
    ) as feature_uploader:
        for sample, df in features_by_specimen.items():
            create_and_transcribe_one_sample(
                sample,
                df,
                feature_uploader,
            )


def create_and_transcribe_one_sample(
    sample: str,
    df: DataFrame,
    feature_uploader: ADIFeaturesUploader,
) -> None:
    for column in df.columns:
        if column.startswith('C '):
            symbol = column[2:]
            criteria = PhenotypeCriteria(positive_markers=[symbol], negative_markers=[])
            value = compute_squidpy_metric_for_one_sample(df, [criteria], 'spatial autocorrelation')
            if value is None:
                continue
            feature_uploader.stage_feature_value((symbol,), sample, value)


def _fetch_cells(
    cursor: Psycopg2Cursor,
    study: str,
) -> dict[str, DataFrame]:
    feature_matrices = FeatureMatrixExtractor(cursor).extract(study=study)
    features_by_specimen = {
        specimen: bundle.dataframe for specimen, bundle in feature_matrices.items()
    }
    return features_by_specimen
