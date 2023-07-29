"""Low-level calculations of squidpy metrics."""

from typing import Any

from numpy.typing import NDArray
from pandas import DataFrame
from squidpy.gr import spatial_neighbors, nhood_enrichment, co_occurrence, ripley
from anndata import AnnData

from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.workflow.common.cell_df_indexer import get_mask


def describe_squidpy_feature_derivation_method():
    return '''
    Calculates nhood_enrichment, co_occurrence, and ripley from squidpy.gr using clusters derived
    from the phenotypes provided. Reference db.squidpy_metrics.convert_df_to_anndata for the
    clustering method.
    '''.lstrip().rstrip()


def compute_squidpy_metrics_for_one_sample(
    df_cell: DataFrame,
    phenotypes: list[PhenotypeCriteria]
) -> dict[
    str,
    dict[str, list[float] | list[int]] |
    dict[str, list[float]] | dict[str, list[list[float]] | list[float] | list[int]]
] | None:
    """Compute Squidpy metrics for a tissue sample with a clustering of the given phenotypes."""
    masks: list[NDArray[Any]] = [get_mask(df_cell, signature) for signature in phenotypes]
    adata = convert_df_to_anndata(df_cell, masks)
    return {
        'nhood_enrichment': _nhood_enrichment(adata),
        'co_occurence': _co_occurrence(adata),
        'ripley': _ripley(adata)
    }


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
    adata = AnnData(obsm={'spatial': locations})
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
    zscore, count = nhood_enrichment(adata, 'cluster', copy=True)
    return {'zscore': zscore.tolist(), 'count': count.tolist()}


def _co_occurrence(adata: AnnData) -> dict[str, list[float]]:
    """Compute co-occurrence probability of clusters."""
    occ, interval = co_occurrence(adata, 'cluster', copy=True)
    return {'occ': occ.tolist(), 'interval': interval.tolist()}


def _ripley(adata: AnnData) -> dict[str, list[list[float]] | list[float] | list[int]]:
    r"""Compute various Ripley\'s statistics for point processes."""
    result = ripley(adata, 'cluster', copy=True)
    return {
        'F_mode': result['F_mode'].to_numpy().to_list(),
        'sims_stat': result['sims_stat'].to_numpy().to_list(),
        'bins': result['bins'].to_list(),
        'pvalues': result['pvalues'].to_list(),
    }
