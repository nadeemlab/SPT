"""Make squidpy metrics that don't require specific phenotype selection available."""

from typing import cast

from pandas import DataFrame
from anndata import AnnData  # type: ignore
from squidpy.gr import spatial_autocorr  # type: ignore
from psycopg2.extensions import cursor as Psycopg2Cursor

from spatialprofilingtoolbox import DatabaseConnectionMaker
from spatialprofilingtoolbox.db.feature_matrix_extractor import FeatureMatrixExtractor
from spatialprofilingtoolbox.db.feature_matrix_extractor import Bundle
from spatialprofilingtoolbox.db.create_data_analysis_study import DataAnalysisStudyFactory
from spatialprofilingtoolbox.workflow.common.squidpy import convert_df_to_anndata
from spatialprofilingtoolbox.workflow.common.export_features import ADIFeaturesUploader
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


def _describe_spatial_autocorr_derivation_method() -> str:
    """Return a description of the spatial autocorrelation derivation method."""
    return 'Global Autocorrelation Statistic (Moran\'s I). See Squidpy documentation for ' \
        'squidpy.gr.spatial_autocorr for more information.'.lstrip().rstrip()


def _spatial_autocorr(data: AnnData, channels: list[str]) -> DataFrame:
    return spatial_autocorr(
        data,
        attr='X',
        mode='moran',
        corr_method=None,
        copy=True,
    )


def create_and_transcribe_squidpy_features(
    database_connection_maker: DatabaseConnectionMaker,
    study: str,
) -> None:
    """Transcribe "off-demand" Squidpy feature(s) in features system."""
    connection = database_connection_maker.get_connection()
    das = DataAnalysisStudyFactory(connection, study, 'spatial autocorrelation').create()
    features_by_specimen = _fetch_cells_and_phenotypes(connection.cursor(), study)
    with ADIFeaturesUploader(
        database_connection_maker,
        data_analysis_study=das,
        derivation_and_number_specifiers=(_describe_spatial_autocorr_derivation_method(), 1),
        impute_zeros=True,
        upload_anyway=True,
    ) as feature_uploader:
        for sample, df in features_by_specimen.items():
            channels = list(set(df.columns).difference(['pixel x', 'pixel y']))
            adata = convert_df_to_anndata(df)
            autocorr_stats = _spatial_autocorr(adata, channels)
            df_index_to_channel = dict(enumerate(df.columns))
            for df_index_value, row in autocorr_stats.iterrows():
                channel = str(df_index_to_channel[int(df_index_value)])
                if channel in {'pixel x', 'pixel y'}:
                    continue
                feature_uploader.stage_feature_value((channel,), sample, row['pval_norm'])


def _fetch_cells_and_phenotypes(
    cursor: Psycopg2Cursor,
    study: str,
) -> dict[str, DataFrame]:
    extractor = FeatureMatrixExtractor(cursor)
    bundle = cast(Bundle, extractor.extract(study=study))
    FeatureMatrices = dict[str, dict[str, DataFrame | str]]
    feature_matrices = cast(FeatureMatrices, bundle[study]['feature matrices'])
    return {
        specimen: cast(DataFrame, packet['dataframe'])
        for specimen, packet in feature_matrices.items()
    }
