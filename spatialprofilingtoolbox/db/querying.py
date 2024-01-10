"""Some basic accessors that retrieve from the database."""
import re

from spatialprofilingtoolbox.db.database_connection import QueryCursor
from spatialprofilingtoolbox.db.exchange_data_formats.study import (
    StudyComponents,
    StudyHandle,
    StudySummary,
)
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import (
    PhenotypeSymbol,
    Channel,
    PhenotypeCriteria,
    UMAPChannel,
    CGGNNImportanceRank,
)
from spatialprofilingtoolbox.db.cohorts import get_cohort_identifiers
from spatialprofilingtoolbox.db.accessors import (
    GraphsAccess,
    StudyAccess,
    PhenotypesAccess,
    UMAPAccess,
)


class QueryHandler:
    """Handle simple queries to the database."""
    @classmethod
    def get_study_components(cls, cursor, study: str) -> StudyComponents:
        return StudyAccess(cursor).get_study_components(study)

    @classmethod
    def retrieve_study_specifiers(cls, cursor) -> list[str]:
        return StudyAccess(cursor).get_study_specifiers()

    @classmethod
    def retrieve_study_handle(cls, cursor, study: str) -> StudyHandle:
        return StudyAccess(cursor).get_study_handle(study)

    @classmethod
    def get_number_cells(cls, cursor, study: str) -> int:
        access = StudyAccess(cursor)
        components = access.get_study_components(study)
        return access.get_number_cells(components.measurement)

    @classmethod
    def get_study_summary(cls, cursor, study: str) -> StudySummary:
        return StudyAccess(cursor).get_study_summary(study)

    @classmethod
    def get_composite_phenotype_identifiers(cls, cursor) -> list[str]:
        return PhenotypesAccess(cursor).get_composite_phenotype_identifiers()

    @classmethod
    def get_phenotype_symbols(cls, cursor, study: str) -> list[PhenotypeSymbol]:
        return PhenotypesAccess(cursor).get_phenotype_symbols(study)

    @classmethod
    def get_phenotype_criteria(cls, cursor, study: str, phenotype_symbol: str) -> PhenotypeCriteria:
        return PhenotypesAccess(cursor).get_phenotype_criteria(study, phenotype_symbol)

    @classmethod
    def retrieve_signature_of_phenotype(cls,
        cursor,
        phenotype_handle: str,
        study: str
    ) -> PhenotypeCriteria:
        channel_names = PhenotypesAccess(cursor).get_channel_names(study)
        components = StudyAccess(cursor).get_study_components(study)
        if phenotype_handle in channel_names:
            return PhenotypeCriteria(positive_markers=[phenotype_handle], negative_markers=[])
        if re.match(r'^\d+$', phenotype_handle):
            return PhenotypesAccess(cursor).get_phenotype_criteria_by_identifier(
                phenotype_handle,
                components.analysis,
            )
        return PhenotypeCriteria(positive_markers=[], negative_markers=[])

    @classmethod
    def get_channel_names(cls, cursor, study: str) -> list[Channel]:
        return [
            Channel(symbol=name)
            for name in PhenotypesAccess(cursor).get_channel_names(study)
        ]

    @classmethod
    def get_umaps_low_resolution(cls, cursor, study: str) -> list[UMAPChannel]:
        access = UMAPAccess(cursor)
        umap_rows = access.get_umap_rows(study)
        return UMAPAccess.downsample_umaps_base64(umap_rows)

    @classmethod
    def get_umap(cls, cursor, study: str, channel: str) -> UMAPChannel:
        return UMAPAccess(cursor).get_umap_row_for_channel(study, channel)

    @classmethod
    def get_cggnn_metrics(cls, cursor, study: str) -> list[CGGNNImportanceRank]:
        return GraphsAccess(cursor).get_metrics(study)

    @classmethod
    def get_important_cells(cls, cursor, study: str, cell_limit: int) -> set[int]:
        return GraphsAccess(cursor).get_important_cells(study, cell_limit)


def query() -> QueryCursor:
    return QueryCursor(QueryHandler)
