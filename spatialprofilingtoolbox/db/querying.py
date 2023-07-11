"""Some basic accessors that retrieve from the database."""
import re

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudyComponents
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudyHandle
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudySummary
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import CellFractionsSummary
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeSymbol
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.db.cohorts import _get_cohort_identifiers
from spatialprofilingtoolbox.db.study_access import _get_study_summary
from spatialprofilingtoolbox.db.study_access import _get_study_handles
from spatialprofilingtoolbox.db.study_access import _get_number_cells
from spatialprofilingtoolbox.db.study_access import _get_study_components
from spatialprofilingtoolbox.db.fractions_and_associations import _get_fractions_rows
from spatialprofilingtoolbox.db.fractions_and_associations import _get_fractions_test_results
from spatialprofilingtoolbox.db.fractions_and_associations import _get_feature_associations
from spatialprofilingtoolbox.db.fractions_and_associations import _create_cell_fractions_summary
from spatialprofilingtoolbox.db.phenotypes import _get_phenotype_symbols
from spatialprofilingtoolbox.db.phenotypes import _get_phenotype_criteria
from spatialprofilingtoolbox.db.phenotypes import _get_channel_names
from spatialprofilingtoolbox.db.phenotypes import _get_phenotype_criteria_by_identifier

def get_study_components(study_name: str) -> StudyComponents:
    with DBCursor() as cursor:
        components = _get_study_components(cursor, study_name)
    return components


def retrieve_study_handles() -> list[StudyHandle]:
    with DBCursor() as cursor:
        handles = _get_study_handles(cursor)
    return handles


def get_number_cells(study: str) -> int:
    with DBCursor() as cursor:
        components = _get_study_components(cursor, study)
        cells=_get_number_cells(cursor, components.measurement)
    return cells


def get_study_summary(study: str) -> StudySummary:
    with DBCursor() as cursor:
        summary = _get_study_summary(cursor, study)
    return summary


def get_cell_fractions_summary(study: str, pvalue: float) -> list[CellFractionsSummary]:
    with DBCursor() as cursor:
        fractions = _get_fractions_rows(cursor, study)
        tests = _get_fractions_test_results(cursor, study)
        cohort_identifiers = _get_cohort_identifiers(cursor, study)
    features = [f.marker_symbol for f in fractions]
    associations = _get_feature_associations(tests, pvalue, cohort_identifiers, features)
    return _create_cell_fractions_summary(fractions, associations)


def get_phenotype_symbols(study: str) -> list[PhenotypeSymbol]:
    with DBCursor() as cursor:
        phenotype_symbols = _get_phenotype_symbols(cursor, study)
    return phenotype_symbols


def get_phenotype_criteria(study: str, phenotype_symbol: str) -> PhenotypeCriteria:
    with DBCursor() as cursor:
        criteria = _get_phenotype_criteria(cursor, study, phenotype_symbol)
    return criteria


def retrieve_signature_of_phenotype(phenotype_handle: str, study: str) -> PhenotypeCriteria:
    with DBCursor() as cursor:
        channel_names = _get_channel_names(cursor, study)
        components = _get_study_components(cursor, study)
    if phenotype_handle in channel_names:
        return PhenotypeCriteria(positive_markers=[phenotype_handle], negative_markers=[])
    if re.match(r'^\d+$', phenotype_handle):
        with DBCursor() as cursor:
            return _get_phenotype_criteria_by_identifier(
                cursor,
                phenotype_handle,
                components.analysis,
            )
    return PhenotypeCriteria(positive_markers=[], negative_markers=[])
