"""Data structures for ready exchange, related to computations or derived metrics."""

from pydantic import BaseModel #pylint: disable=no-name-in-module

class CellFractionsSummary(BaseModel):
    """
    Summary of a cell fractions feature of the sample set, including "report" of significantly
    associated cohorts.
    """
    phenotype: str
    sample_cohort: str
    significantly_different_cohorts: list[str]
    average_percent: float


class CellFractionsAverage(BaseModel):
    """Average cell fractions for a feature."""
    marker_symbol: str
    multiplicity: str
    stratum_identifier: str
    average_percent: float


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
    """
    The criteria defining a given "comopsite" phenotype in terms of expression or non-expression of
    given markers.
    """
    positive_markers: list[str]
    negative_markers: list[str]


class CompositePhenotype(BaseModel):
    """
    For named phenotypes, the name and the internal identifier used for matching up related records.
    """
    name: str
    identifier: str
    criteria: PhenotypeCriteria


class PhenotypeCount(BaseModel):
    """
    The number of cells (and formatted/rounded percentage or fraction) in a given specimen,
    belonging to some specific class.
    """
    specimen: str
    count: int
    percentage: float


class PhenotypeCounts(BaseModel):
    """The number of cells of a given phenotype across all samples in a given study."""
    counts: list[PhenotypeCount]
    phenotype: CompositePhenotype
    number_cells_in_study: int


class ProximityMetricsComputationResult(BaseModel):
    """
    The response to a request for retrieval of proximity metrics in some specific case. This request
    may also be a request for computation of these metrics in the background (which may be pending).
    """
    values: dict[str, float | None]
    is_pending: bool


class UMAPChannel(BaseModel):
    """
    A UMAP dimensional reduction of a cell set, with one intensity channel's overlay.
    The image is encoded in base 64.
    """
    channel: str
    base64_png: str
