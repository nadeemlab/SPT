"""Selected metrics from the squidpy library, adapted for use with SPT."""

from typing import Any

from numpy.typing import NDArray
from pandas import DataFrame
from squidpy.gr import nhood_enrichment, co_occurrence, ripley
from anndata import AnnData

from spatialprofilingtoolbox.db.squidpy_metrics import convert_df_to_anndata
from spatialprofilingtoolbox.ondemand.providers import Provider


class SquidpyProvider(Provider):
    """Calculate select squidpy metrics."""

    def __init__(self, data_directory: str, load_centroids: bool = False) -> None:
        """Load from a precomputed JSON artifact in the data directory.

        Note: SquidpyProvider always loads centroids because it needs them.
        """
        super().__init__(data_directory, load_centroids=True)
        self.anndata: dict[str, dict[str, AnnData]] = {}

    def prepare_anndata(self, phenotypes_to_cluster_on: list[str]) -> None:
        """Convert DataFrames to AnnData objects for squidpy use.

        Reference db.squidpy_metrics.convert_df_to_anndata for phenotypes_to_cluster_on.
        """
        for study_name in self.get_study_names():
            self.anndata[study_name] = {}
            for specimen, df in self.data_arrays[study_name].items():
                self.anndata[study_name][specimen] = convert_df_to_anndata(
                    df, phenotypes_to_cluster_on)

    def nhood_enrichment(self) -> dict[str, dict[str, dict[str, NDArray[Any]]]]:
        """Compute neighborhood enrichment by permutation test."""
        results: dict[str, dict[str, dict[str, NDArray[Any]]]] = {}
        for study, specimen_anndata in self.anndata.items():
            results[study] = {}
            for specimen, adata in specimen_anndata.items():
                zscore, count = nhood_enrichment(adata, 'cluster', copy=True)
                results[study][specimen] = {'zscore': zscore, 'count': count}
        return results

    def co_occurrence(self) -> dict[str, dict[str, dict[str, NDArray[Any]]]]:
        """Compute co-occurrence probability of clusters."""
        results: dict[str, dict[str, dict[str, NDArray[Any]]]] = {}
        for study, specimen_anndata in self.anndata.items():
            results[study] = {}
            for specimen, adata in specimen_anndata.items():
                occ, interval = co_occurrence(adata, 'cluster', copy=True)
                results[study][specimen] = {'occ': occ, 'interval': interval}
        return results

    def ripley(self) -> dict[str, dict[str, dict[str, DataFrame | NDArray[Any]]]]:
        r"""Compute various Ripley\'s statistics for point processes."""
        results: dict[str, dict[str, dict[str, DataFrame | NDArray[Any]]]] = {}
        for study, specimen_anndata in self.anndata.items():
            results[study] = {}
            for specimen, adata in specimen_anndata.items():
                results[study][specimen] = ripley(adata, 'cluster', copy=True)
        return results
