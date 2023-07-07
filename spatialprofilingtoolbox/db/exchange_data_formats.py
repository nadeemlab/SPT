"""Data structures for ready exchange, representing phenotypes, cells, etc."""

from pydantic import BaseModel #pylint: disable=no-name-in-module


class StudyComponents(BaseModel):
    """Main substudies of a primary study."""
    collection: str
    measurement: str
    analysis: str


class Institution(BaseModel):
    """An institution, e.g. research organization in which a study took place."""
    name: str


class Assay(BaseModel):
    """The method of assessment for a specific feature. "Modality"."""
    name: str


class StudyContact(BaseModel):
    """Contact information for a person to contact regarding a study."""
    name: str
    email_address: str


class DataRelease(BaseModel):
    """Location and publication information about a release/publication of a dataset."""
    repository: str
    url: str
    date: str


class Publication(BaseModel):
    """Dates, authorship, etc. for a published article."""
    title: str
    url: str
    first_author_name: str
    date: str


class CountsSummary(BaseModel):
    """
    Counts summary of samples, cells, etc. for quick availability without retrieval of
    objects/records themselves.
    """
    specimens: int
    cells: int
    channels: int
    composite_phenotypes: int


class Cohort(BaseModel):
    """A cohort/stratum in the primary stratification for a study, if available."""
    identifier: int
    temporality: str
    diagnosis: str
    result: str


class CohortAssignment(BaseModel):
    """One sample assignment, see SampleCohorts."""
    sample: str
    cohort: int


class SampleCohorts(BaseModel):
    """The primary cohort stratification for a study, if one is available."""
    assignments: list[CohortAssignment]
    cohorts: list[Cohort]


class Context(BaseModel):
    """The context in which a study was performed."""
    institution: Institution
    assay: Assay
    contact: StudyContact


class Products(BaseModel):
    """Formal research products of a given study."""
    data_release: DataRelease
    publication: Publication


class StudySummary(BaseModel):
    """Convenience summary of a given study."""
    context: Context
    products: Products
    counts: CountsSummary
    cohorts: SampleCohorts


class CellFractionsSummary(BaseModel):
    """Summary of a cell fractions feature of the sample set."""
    phenotype: str
    sample_cohort: int
    significantly_different_cohorts: list[int]
    average_percent: float


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
    values: dict[str, float]
    is_pending: bool


class UMAPChannel(BaseModel):
    """
    A UMAP dimensional reduction of a cell set, with one intensity channel's overlay.
    The image is encoded in base 64.
    """
    channel: str
    base64_svg: str


class UMAPHighResolution(BaseModel):
    """A high-resolution raster image of one of the UMAP visualizations."""
    channel: str
    base64_png: str
