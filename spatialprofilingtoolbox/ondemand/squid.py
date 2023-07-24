"""Selected metrics from the squidpy library, adapted for use with SPT."""

from typing import Optional, Any

from numpy import ndarray
from numpy.typing import NDArray
from pandas import DataFrame
from squidpy.gr import spatial_neighbors, nhood_enrichment, co_occurrence, ripley, spatial_autocorr
from anndata import AnnData


def prepare_data(df: DataFrame, phenotypes_to_cluster_on: Optional[list[str]]) -> AnnData:
    """Convert SPT DataFrame to AnnData object.

    Parameters:
        df: DataFrame
            A dataframe with an arbitrary index, x and y locations of histological structures with
            column names 'x' and 'y', and, optionally, several columns with arbitrary names each
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
    if len(phenotypes_to_cluster_on) == 0:
        phenotypes_to_cluster_on = None
    locations: ndarray = df[['x', 'y']].to_numpy()
    phenotype_expression: DataFrame = df.delete(['x', 'y'], axis=1)
    if phenotypes_to_cluster_on is not None:
        clustering = phenotype_expression[phenotypes_to_cluster_on[0]].astype(
            int)
        i_cluster = 2
        for phenotype in phenotypes_to_cluster_on[1:]:
            clustering[phenotype_expression[phenotype]
                       & (clustering == 0)] = i_cluster
            i_cluster += 1
        phenotype_expression['cluster'] = clustering
    # TODO: Consider allowing for multiple clustering arrangements?
    data = AnnData(obs=phenotype_expression, obsm={'spatial': locations})
    spatial_neighbors(data)
    return data


def single_metrics(data: AnnData) -> tuple[NDArray[Any], NDArray[Any], NDArray[Any]]:
    """Return all selected squidpy metrics that don't require an explicit clustering."""
    return _spatial_autocorr(data)


def clustered_metrics(data: AnnData) -> tuple[
    tuple[NDArray[Any], NDArray[Any]],
    tuple[NDArray[Any], NDArray[Any]],
    tuple[DataFrame, DataFrame, NDArray[Any], NDArray[Any]],
]:
    """Return all selected metrics that require an stated clustering."""
    if 'cluster' not in data.obs.columns:
        raise ValueError(
            'Provided data is missing information about clusters.')
    return _nhood_enrichment(data), _co_occurrence(data), _ripley(data)


def _nhood_enrichment(data: AnnData) -> tuple[NDArray[Any], NDArray[Any]]:
    zscore, count = nhood_enrichment(data, 'cluster', copy=True)
    return zscore, count


def _co_occurrence(data: AnnData) -> tuple[NDArray[Any], NDArray[Any]]:
    occ, interval = co_occurrence(data, 'cluster', copy=True)
    return occ, interval


def _ripley(data: AnnData) -> tuple[DataFrame, DataFrame, NDArray[Any], NDArray[Any]]:
    ripley_metrics = ripley(data, 'cluster', copy=True)
    f_stat: DataFrame = ripley_metrics['f_stat']
    sims_stat: DataFrame = ripley_metrics['sims_stat']
    bins: ndarray = ripley_metrics['bins']
    pvalues: ndarray = ripley_metrics['pvalues']
    return f_stat, sims_stat, bins, pvalues


def _spatial_autocorr(data: AnnData) -> tuple[NDArray[Any], NDArray[Any], NDArray[Any]]:
    data.obs.columns
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
