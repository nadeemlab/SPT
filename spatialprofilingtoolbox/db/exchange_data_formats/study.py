"""Data structures for ready exchange, related to an overall study."""

from pydantic import BaseModel


class StudyComponents(BaseModel):
    """Main substudies of a primary study."""
    collection: str
    measurement: str
    analysis: str


class StudyHandle(BaseModel):
    """A study specifier (or handle), together with an extended for-display variant."""
    handle: str
    display_name_detail: str
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Dataset ABC",
                    "display_name_detail": "Dataset ABC - Nature 2030"
                }
            ]
        }
    }


class Institution(BaseModel):
    """
    The institution, for example a research organization, in which a study took place or in which
    the study was carried out.
    """
    name: str
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                }
            ]
        }
    }


class Assay(BaseModel):
    """
    This is a minimal tag indicating the method of assessment or measurement of feature data. This
    may sometimes be called data "modality".
    """
    name: str
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                }
            ]
        }
    }


class StudyContact(BaseModel):
    """
    This is contact information for a person who is at least semi-formally responsible for fielding
    inquiries regarding the study and/or its data products, due to being listed as a lead author
    or research group leader or similar.
    """
    name: str
    email_address: str
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                }
            ]
        }
    }


class DataRelease(BaseModel):
    """
    This is basic information about a published/released dataset, sufficient for an application to
    provide a reasonable reference that a user could follow up on via the URL for more detail.
    """
    repository: str
    url: str
    date: str
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                }
            ]
        }
    }


class Publication(BaseModel):
    """
    This is basic information about a published article, sufficient for an application to provide
    a reasonable reference that a user could follow via the URL for more detail. So the longevity
    of the reference function is dependent on that of the URL.
    """
    title: str
    url: str
    first_author_name: str
    date: str
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                }
            ]
        }
    }


class CountsSummary(BaseModel):
    """
    This is a summary including the number of samples, cells, channels, and pre-defined combinations
    ("composite phenotypes"). This is provided for convenience, without requiring review of the
    per-sample values.
    """
    specimens: int
    cells: int
    channels: int
    composite_phenotypes: int
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                }
            ]
        }
    }


class Cohort(BaseModel):
    """
    This is a cohort or stratum in the primary stratification for a study, if available.
    Often a cohort may be defined by a *diagnosis* event and diagnosis *result*, sometimes with a
    *temporality* indicating something about when the event took place.

    The *identifier* field is used for reference.
    """
    identifier: str
    temporality: str
    diagnosis: str
    result: str
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                }
            ]
        }
    }


class CohortAssignment(BaseModel):
    """This is one assignment of a sample to a cohort."""
    sample: str
    cohort: str
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                }
            ]
        }
    }


class SampleCohorts(BaseModel):
    """
    This is the primary cohort stratification for a study, if one is available, often used to state
    the primary findings.
    """
    assignments: list[CohortAssignment]
    cohorts: list[Cohort]
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                }
            ]
        }
    }


class Context(BaseModel):
    """These are a few annotations of the context or manner in which a study was performed."""
    institution: Institution
    assay: Assay
    contact: StudyContact
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                }
            ]
        }
    }


class Products(BaseModel):
    """These are the formal research products of a given study."""
    data_release: DataRelease
    publication: Publication
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                }
            ]
        }
    }


class StudySummary(BaseModel):
    """This is a convenience aggregation of summary and metadata for a given study."""
    context: Context
    products: Products
    counts: CountsSummary
    cohorts: SampleCohorts
    findings: list[str]
    has_umap: bool
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                }
            ]
        }
    }
