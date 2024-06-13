"""Represent one job."""

from attrs import define

@define
class ComputationJobReference:
    """Represent one job."""
    feature_specification: int
    study: str
    sample: str
