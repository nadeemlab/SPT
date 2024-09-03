"""Data structures for ready exchange, related to an overall study."""

from pydantic import BaseModel #pylint: disable=no-name-in-module

class StudyComponents(BaseModel):
    """Main substudies of a primary study."""
    collection: str
    measurement: str
    analysis: str


class StudyHandle(BaseModel):
    """A study specifier (or handle), together with additional information to display in the context
    of an item header/label.
    """
    handle: str
    display_name_detail: str


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
    """Counts summary of samples, cells, etc. for quick availability without retrieval of
    objects/records themselves.
    """
    specimens: int
    cells: int
    channels: int
    composite_phenotypes: int


class Cohort(BaseModel):
    """A cohort/stratum in the primary stratification for a study, if available."""
    identifier: str
    temporality: str
    diagnosis: str
    result: str


class CohortAssignment(BaseModel):
    """One sample assignment, see SampleCohorts."""
    sample: str
    cohort: str


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
    findings: list[str]
    has_umap: bool
