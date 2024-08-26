"""Data structures for ready exchange, related to computations or derived metrics."""

from pydantic import BaseModel  # pylint: disable=no-name-in-module

from spatialprofilingtoolbox.graphs.plugin_constants import GNNPlugin


class FeatureAssociationTest(BaseModel):
    """One test for association between two cohorts along a feature."""
    feature: str
    cohort1: str
    cohort2: str
    pvalue: float


class PhenotypeSymbol(BaseModel):
    """The display/handle string and the internal identifier for a phenotype."""
    handle_string: str
    identifier: str


class Channel(BaseModel):
    """The symbol for one of the imaged or measured channels.."""
    symbol: str


class PhenotypeCriteria(BaseModel):
    """Criteria defining a "composite" phenotype by expression and non-expression of markers."""
    positive_markers: tuple[str, ...]
    negative_markers: tuple[str, ...]


class PhenotypeSymbolAndCriteria(BaseModel):
    """The display/handle string and the internal identifier for a phenotype."""
    handle_string: str
    identifier: str
    criteria: PhenotypeCriteria


class CompositePhenotype(BaseModel):
    """For named phenotypes, the name and the internal identifier used for matching up related
    records.
    """
    name: str
    identifier: str
    criteria: PhenotypeCriteria


class PhenotypeCount(BaseModel):
    """The number of cells (and formatted/rounded percentage or fraction) in a given specimen,
    belonging to some specific class.
    """
    specimen: str
    count: int | None
    percentage: float | None


class PhenotypeCounts(BaseModel):
    """The number of cells of a given phenotype across all samples in a given study."""
    counts: tuple[PhenotypeCount, ...]
    phenotype: CompositePhenotype
    number_cells_in_study: int
    is_pending: bool


class UnivariateMetricsComputationResult(BaseModel):
    """The response to a request for retrieval of derived/computed metrics (typically a spatially-
    enrich feature), or a request for such metrics to be computed as a background job.
    """
    values: dict[str, float | None]
    is_pending: bool


class CellData(BaseModel):
    """Cell-level data including position and phenotype information, for a single sample.
    """
    feature_names: list[str]
    cells: list[list[str | float | int]]


class AvailableGNN(BaseModel):
    """List of available GNN metrics, i.e. which plugins were used in a completed run."""
    plugins: tuple[GNNPlugin, ...]
