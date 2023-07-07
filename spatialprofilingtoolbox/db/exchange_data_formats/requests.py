"""Data structures for ready exchange, related to reqeuests for data."""

from pydantic import BaseModel #pylint: disable=no-name-in-module

class PhenotypeCriteriaRequest(BaseModel):
    """
    A request for the criteria defining a specific named phenotype in the context of a given study.
    """
    study: str
    phenotype_name: str


class PhenotypeCountsRequest(BaseModel):
    """
    A request for the number of cells of a given specified phenotype, across samples in a given
    study.
    """
    