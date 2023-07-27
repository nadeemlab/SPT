"""Make squidpy metrics that don't require specific phenotype selection available."""

from typing import Any

from numpy.typing import NDArray
from pandas import DataFrame
from anndata import AnnData
from squidpy.gr import spatial_autocorr, spatial_neighbors

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.db.feature_matrix_extractor import FeatureMatrixExtractor
from spatialprofilingtoolbox.db.create_data_analysis_study import DataAnalysisStudyFactory
from spatialprofilingtoolbox.workflow.common.export_features import ADIFeaturesUploader
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


def _describe_spatial_autocorr_derivation_method() -> str:
    """Return a description of the spatial autocorrelation derivation method."""
    return 'Global Autocorrelation Statistic (Moran\'s I). See Squidpy documentation for ' \
        'squidpy.gr.spatial_autocorr for more information.'.lstrip().rstrip()


def convert_df_to_anndata(
    df: DataFrame,
    phenotypes_to_cluster_on: list[str] | None = None,
) -> AnnData:
    """Convert SPT DataFrame to AnnData object for use with Squidpy metrics.

    Parameters:
        df: DataFrame
            A dataframe with an arbitrary index, x and y locations of histological structures with
            column names 'pixel x' and 'pixel y', and several columns with arbitrary names each
            indicating the expression of a phenotype.
        phenotypes_to_cluster_on: list[str] | None
            Used to create a 'cluster' column in the AnnData object if provided.
            * If only one phenotype is provided, two clusters will be created mirroring the
                presence or absence of the phenotype in each histological structure.
            * If more than one is provided, the first cluster will be selected based on the
                presence of the first phenotype in each histological structure, while the second
                cluster will be selected only among histological structures that did not have the
                first phenotype, with the pattern continuing for each successive phenotype.
                Histological structures that do not have any of the phenotypes will be assigned to
                cluster 0. 
    """
    locations: NDArray[Any] = df[['pixel x', 'pixel y']].to_numpy()
    phenotype_expression: DataFrame = df.drop(['pixel x', 'pixel y'], axis=1)
    if (phenotypes_to_cluster_on is not None) and (len(phenotypes_to_cluster_on) > 0):
        clustering = phenotype_expression[phenotypes_to_cluster_on[0]].astype(
            int)
        i_cluster = 2
        for phenotype in phenotypes_to_cluster_on[1:]:
            clustering[phenotype_expression[phenotype]
                       & (clustering == 0)] = i_cluster
            i_cluster += 1
        phenotype_expression['cluster'] = clustering.astype('category')
    # TODO: Consider allowing for multiple clustering arrangements?
    data = AnnData(obs=phenotype_expression, obsm={'spatial': locations})
    spatial_neighbors(data)
    return data


def _spatial_autocorr(data: AnnData) -> tuple[NDArray[Any], NDArray[Any], NDArray[Any]]:
    autocorr_metrics: DataFrame = spatial_autocorr(
        data,
        attr='obs',
        genes=data.obs.drop('cluster', axis=1).columns.tolist(),
        corr_method=None,
        copy=True,
    )
    i_statistic = autocorr_metrics['I'].to_numpy()
    pval_z_sim = autocorr_metrics['pval_z_sim'].to_numpy()
    pval_sim = autocorr_metrics['pval_sim'].to_numpy()
    return i_statistic, pval_z_sim, pval_sim


def create_and_transcribe_squidpy_features(
    database_connection_maker: DatabaseConnectionMaker,
    study: str
) -> None:
    """Transcribe "off-demand" Squidpy feature(s) in features system."""
    connection = database_connection_maker.get_connection()
    features_by_specimen = _fetch_cells_and_phenotypes(
        database_connection_maker, study)
    for sample, df in features_by_specimen.items():
        adata = convert_df_to_anndata(df)
        autocorr_stats = _spatial_autocorr(adata)
        das = DataAnalysisStudyFactory(
            connection, study, 'spatial autocorrelation').create()
        with ADIFeaturesUploader(
            database_connection_maker,
            data_analysis_study=das,
            derivation_and_number_specifiers=(
                _describe_spatial_autocorr_derivation_method(), 1),
            impute_zeros=True,
        ) as feature_uploader:
            value = autocorr_stats
            for specifier, value in zip(['thing', 'thing'], autocorr_stats):
                feature_uploader.stage_feature_value(
                    (specifier,), sample, value)


def _fetch_cells_and_phenotypes(
    database_connection_maker: DatabaseConnectionMaker,
    study: str
) -> dict[str, DataFrame]:
    study_data: dict[str, dict[str, DataFrame | str]] = FeatureMatrixExtractor.extract(
        database_connection_maker, study=study)[study]['feature_matrices']
    return {specimen: packet['dataframe'] for specimen, packet in study_data.items()}
