"""Low-level calculations of squidpy metrics."""

from typing import Any
from typing import cast

from numpy.typing import NDArray
from pandas import DataFrame
from squidpy.gr import spatial_neighbors, nhood_enrichment, co_occurrence, ripley  # type: ignore
from anndata import AnnData  # type: ignore
from scipy.stats import norm  # type: ignore

from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.workflow.common.cell_df_indexer import get_mask
from spatialprofilingtoolbox.ondemand import squidpy_feature_classnames_descriptions

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)

def describe_squidpy_feature_derivation_method(feature_class: str) -> str | None:
    if feature_class in squidpy_feature_classnames_descriptions:
        return squidpy_feature_classnames_descriptions[feature_class]
    return None


def lookup_squidpy_feature_class(method: str) -> str | None:
    for key, _method in squidpy_feature_classnames_descriptions.items():
        if method == _method:
            return key
    return None


def compute_squidpy_metric_for_one_sample(
    df_cell: DataFrame,
    phenotypes: list[PhenotypeCriteria],
    feature_class: str,
    radius: float | None = None,
) -> float | None:
    """Compute Squidpy metrics for a tissue sample with a clustering of the given phenotypes."""
    df_cell.sort_index(inplace=True)
    masks: list[NDArray[Any]] = [get_mask(df_cell, signature) for signature in phenotypes]
    adata = convert_df_to_anndata(df_cell, masks)
    match feature_class:
        case 'neighborhood enrichment':
            return summarize_neighborhood_enrichment(_nhood_enrichment(adata))
        case 'co-occurrence':
            if radius is None:
                raise ValueError('You must supply radius value for co-occurrence metric.')
            return summarize_co_occurrence(_co_occurrence(adata, radius))
        case 'ripley':
            return summarize_ripley(_ripley(adata))
    return None


def summarize_neighborhood_enrichment(unstructured_metrics) -> float | None:
    zscore = float(unstructured_metrics['zscore'][0][1])
    return float(norm.cdf(zscore))


def summarize_co_occurrence(unstructured_metrics) -> float | None:
    occurrence_ratios = unstructured_metrics['occ']
    return float(occurrence_ratios[0][1][0])


def summarize_ripley(unstructured_metrics) -> float | None:
    return 3


def convert_df_to_anndata(
    df: DataFrame,
    phenotypes_to_cluster_on: list[NDArray[Any]] | None = None,
) -> AnnData:
    """Convert SPT DataFrame to AnnData object for use with Squidpy metrics.

    Parameters:
        df: DataFrame
            A dataframe with an arbitrary index, x and y locations of histological structures with
            column names 'pixel x' and 'pixel y', and several columns with arbitrary names each
            indicating the expression of a phenotype.
        phenotypes_to_cluster_on: list[NDArray[Any]] | None
            Used to create a 'cluster' column in the AnnData object if provided. Each list is a
            mask of positive or negative features that indicate the phenotype.
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
    adata = AnnData(df.to_numpy(), obsm={'spatial': locations})
    spatial_neighbors(adata)
    if (phenotypes_to_cluster_on is not None) and (len(phenotypes_to_cluster_on) > 0):
        clustering = phenotypes_to_cluster_on[0].astype(int)
        i_cluster = 2
        for phenotype in phenotypes_to_cluster_on[1:]:
            clustering[(clustering == 0) & phenotype] = i_cluster
            i_cluster += 1
        adata.obs['cluster'] = clustering
        adata.obs['cluster'] = adata.obs['cluster'].astype('category')
    return adata


def _nhood_enrichment(adata: AnnData) -> dict[str, list[float] | list[int]]:
    """Compute neighborhood enrichment by permutation test."""
    result = nhood_enrichment(adata, 'cluster', copy=True, seed=128, show_progress_bar=False)
    zscore, count = cast(tuple[NDArray[Any], NDArray[Any]], result)
    return {'zscore': zscore.tolist(), 'count': count.tolist()}


def _co_occurrence(adata: AnnData, radius: float) -> dict[str, list[float]]:
    """Compute co-occurrence probability of clusters."""
    result = co_occurrence(
        adata,
        'cluster',
        copy=True,
        interval=[0.0, radius],  # type: ignore
        show_progress_bar=False,
    )
    occ, interval = cast(tuple[NDArray[Any], NDArray[Any]], result)
    return {'occ': occ.tolist(), 'interval': interval.tolist()}


def _ripley(adata: AnnData) -> dict[str, list[list[float]] | list[float] | list[int]]:
    r"""Compute various Ripley\'s statistics for point processes."""
    result = ripley(adata, 'cluster', copy=True)

    # print(dumps({
    #     'F_mode': result['F_mode'].to_numpy().to_list(),
    #     'sims_stat': result['sims_stat'].to_numpy().to_list(),
    #     'bins': result['bins'].to_list(),
    #     'pvalues': result['pvalues'].to_list(),
    # }, indent=4))

    return {
        'F_mode': result['F_mode'].to_numpy().to_list(),
        'sims_stat': result['sims_stat'].to_numpy().to_list(),
        'bins': result['bins'].to_list(),
        'pvalues': result['pvalues'].to_list(),
    }
