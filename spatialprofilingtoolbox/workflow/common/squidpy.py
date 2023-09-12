"""Low-level calculations of squidpy metrics."""

from typing import Any
from typing import cast
from warnings import warn

from numpy.typing import NDArray
from numpy import isnan
from pandas import DataFrame, Series
from squidpy.gr import (  # type: ignore
    spatial_neighbors,
    nhood_enrichment,
    co_occurrence,
    ripley,
    spatial_autocorr,
)

from anndata import AnnData  # type: ignore
from scipy.stats import norm  # type: ignore

from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox import get_feature_description
from spatialprofilingtoolbox import squidpy_feature_classnames


def lookup_squidpy_feature_class(method: str) -> str | None:
    for key in squidpy_feature_classnames():
        if get_feature_description(key) == method:
            return key
    return None


def compute_squidpy_metric_for_one_sample(
    df_cell: DataFrame,
    phenotypes: list[PhenotypeCriteria],
    feature_class: str,
    radius: float | None = None,
) -> float | None:
    """Compute Squidpy metrics for a tissue sample with a clustering of the given phenotypes."""
    df_cell = df_cell.rename({
        column: (column[2:] if (column.startswith('C ') or column.startswith('P ')) else column)
        for column in df_cell.columns
    }, axis=1)
    masks: list[Series] = [
        (df_cell.astype(bool)[signature.positive_markers].all(axis=1) &
         (~(df_cell.astype(bool))[signature.negative_markers]).all(axis=1))
        for signature in phenotypes
    ]
    adata = convert_df_to_anndata(df_cell, masks)
    match feature_class:
        case 'neighborhood enrichment':
            return _summarize_neighborhood_enrichment(_nhood_enrichment(adata))
        case 'co-occurrence':
            if radius is None:
                raise ValueError('You must supply radius value for co-occurrence metric.')
            return _summarize_co_occurrence(_co_occurrence(adata, radius))
        case 'ripley':
            return _summarize_ripley(_ripley(adata))
        case 'spatial autocorrelation':
            return _summarize_spatial_autocorrelation(_spatial_autocorr(adata))
    return None


def _summarize_neighborhood_enrichment(
    unstructured_metrics: dict[str, NDArray[Any]]
) -> float | None:
    if len(unstructured_metrics['zscore'].shape) != 2:
        return None
    zscore = float(unstructured_metrics['zscore'][0][1])
    return float(norm.cdf(zscore))


def _summarize_co_occurrence(unstructured_metrics: dict[str, NDArray[Any]] | None) -> float | None:
    if unstructured_metrics is None:
        return None
    occurrence_ratios = unstructured_metrics['occ']
    if len(occurrence_ratios.shape) != 3:
        return None
    return float(occurrence_ratios[0][1][0])


def _summarize_ripley(unstructured_metrics: dict[str, NDArray[Any]]) -> float | None:
    bins = unstructured_metrics['bins']
    pvalues = unstructured_metrics['pvalues']
    pairs = list(zip(bins.tolist(), pvalues.tolist()))
    if len(bins) != len(pvalues) or len(pairs) == 0:
        return None
    filtered = [pair for pair in pairs if pair[1] > 0]
    if len(filtered) == 0:
        return 1.0
    sorted_pairs = sorted(filtered, key=lambda pair: pair[1])
    return float(sorted_pairs[0][1])


def _summarize_spatial_autocorrelation(unstructured_metrics: DataFrame) -> float | None:
    row = unstructured_metrics.iloc[0]
    pvalue = float(row['pval_norm'])
    if isnan(pvalue):
        return None
    if pvalue == 0:
        return None
    return round10(pvalue)


def round10(value):
    return int(pow(10, 10) * value) / pow(10, 10)


def convert_df_to_anndata(
    df: DataFrame,
    phenotypes_to_cluster_on: list[Series] | None = None,
) -> AnnData:
    """Convert SPT DataFrame to AnnData object for use with Squidpy metrics.

    Parameters:
        df: DataFrame
            A dataframe with an arbitrary index, x and y locations of histological structures with
            column names 'pixel x' and 'pixel y', and several columns with arbitrary names each
            indicating the expression of a phenotype.
        phenotypes_to_cluster_on: list[Series] | None
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
    adata = AnnData(
        df.drop(['pixel x', 'pixel y'], axis=1).to_numpy(),
        obsm={'spatial': locations},  # type: ignore
    )
    spatial_neighbors(adata)
    if (phenotypes_to_cluster_on is not None) and (len(phenotypes_to_cluster_on) > 0):
        clustering = phenotypes_to_cluster_on[0].astype(int)
        i_cluster = 2
        for phenotype in phenotypes_to_cluster_on[1:]:
            clustering[(clustering == 0) & phenotype] = i_cluster
            i_cluster += 1
        adata.obs['cluster'] = clustering.to_numpy()
        adata.obs['cluster'] = adata.obs['cluster'].astype('category')
        if adata.obs['cluster'].nunique() == 1:
            warn('All phenotypes provided had identical values. Only one cluster could be made.')
    return adata


def _nhood_enrichment(adata: AnnData) -> dict[str, NDArray[Any]]:
    """Compute neighborhood enrichment by permutation test."""
    result = nhood_enrichment(adata, 'cluster', copy=True, seed=128, show_progress_bar=False)
    zscore, count = cast(tuple[NDArray[Any], NDArray[Any]], result)
    return {'zscore': zscore, 'count': count}


def _co_occurrence(adata: AnnData, radius: float) -> dict[str, NDArray[Any]] | None:
    """Compute co-occurrence probability of clusters."""
    if adata.obs['cluster'].nunique() < 2:
        return None
    result = co_occurrence(
        adata,
        'cluster',
        copy=True,
        interval=[0.0, radius],  # type: ignore
        show_progress_bar=False,
    )
    occ, interval = cast(tuple[NDArray[Any], NDArray[Any]], result)
    return {'occ': occ, 'interval': interval}


def _ripley(adata: AnnData) -> dict[str, NDArray[Any]]:
    r"""Compute various Ripley\'s statistics for point processes."""
    result = ripley(adata, 'cluster', copy=True)
    bins = cast(NDArray[Any], result['bins'])
    pvalues = cast(NDArray[Any], result['pvalues'])
    return {
        'bins': bins,
        'pvalues': pvalues[0,],
    }


def _spatial_autocorr(adata: AnnData) -> DataFrame:
    result = spatial_autocorr(
        adata,
        attr='obs',
        genes='cluster',
        mode='moran',
        corr_method=None,
        seed=128,
        copy=True,
    )
    return result
