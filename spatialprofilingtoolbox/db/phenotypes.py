"""Convenience accessors/manipulators for phenotype data."""
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeSymbol
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.db.study_access import _get_study_components


def _get_phenotype_symbols(cursor, study: str) -> list[PhenotypeSymbol]:
    components = _get_study_components(cursor, study)
    query = '''
    SELECT DISTINCT cp.symbol, cp.identifier
    FROM cell_phenotype_criterion cpc
    JOIN cell_phenotype cp ON cpc.cell_phenotype=cp.identifier
    WHERE cpc.study=%s
    ORDER BY cp.symbol
    ;
    '''
    cursor.execute(query, (components.analysis,))
    rows = cursor.fetchall()
    return [
        PhenotypeSymbol(handle_string=row[0], identifier=row[1])
        for row in rows
    ]


class PhenotypeNotFoundError(Exception):
    """
    Raised when information is requested for a phenotype that cannot be located by the given name.
    """


def _get_phenotype_criteria(cursor, study: str, phenotype_symbol: str) -> PhenotypeCriteria:
    query = '''
    SELECT cs.symbol, cpc.polarity
    FROM cell_phenotype_criterion cpc
    JOIN cell_phenotype cp ON cpc.cell_phenotype = cp.identifier
    JOIN chemical_species cs ON cs.identifier = cpc.marker
    JOIN study_component sc ON sc.component_study=cpc.study
    WHERE cp.symbol=%s AND sc.primary_study=%s
    ;
    '''
    cursor.execute(query, (phenotype_symbol, study),)
    rows = cursor.fetchall()
    if len(rows) == 0:
        singles_query = '''
        SELECT symbol, 'positive' as polarity FROM chemical_species
        WHERE symbol=%s
        ;
        '''
        cursor.execute(singles_query, (phenotype_symbol,))
        rows = cursor.fetchall()
        if len(rows) == 0:
            raise PhenotypeNotFoundError(phenotype_symbol)
    positive_markers = sorted([
        marker for marker, polarity in rows if polarity == 'positive'
    ])
    negative_markers = sorted([
        marker for marker, polarity in rows if polarity == 'negative'
    ])
    return PhenotypeCriteria(positive_markers=positive_markers, negative_markers=negative_markers)
