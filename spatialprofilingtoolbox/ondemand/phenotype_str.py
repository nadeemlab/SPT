"""Helper functions for translating phenotype definition strings."""

from ast import literal_eval

from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria


def phenotype_to_phenotype_str(phenotype: PhenotypeCriteria) -> str:
    """Convert phenotype criteria to a controlled string format."""
    return str((tuple(phenotype.positive_markers), tuple(phenotype.negative_markers)))


def phenotype_str_to_phenotype(phenotype_str: str) -> PhenotypeCriteria:
    """Convert controlled phenotype string into a PhenotypeCriteria object."""
    parts = literal_eval(phenotype_str)
    return PhenotypeCriteria(positive_markers=parts[0], negative_markers=parts[1])
