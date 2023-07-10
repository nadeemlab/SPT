"""Convenience accessors/manipulators of cell fractions features and their associations."""
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import CellFractionsSummary
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import CellFractionsAverage
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import FeatureAssociationTest
from spatialprofilingtoolbox.db.study_access import _get_study_components
from spatialprofilingtoolbox.db.cohorts import _replace_stratum_identifiers
from spatialprofilingtoolbox.db.fractions_transcriber import \
    describe_fractions_feature_derivation_method


def _get_fractions_rows(cursor, study: str) -> list[CellFractionsAverage]:
    components = _get_study_components(cursor, study)
    cursor.execute('''
        SELECT marker_symbol, multiplicity, stratum_identifier, average_percent
        FROM fraction_stats
        WHERE measurement_study=%s
            AND data_analysis_study in (%s, \'none\')
        ORDER BY multiplicity, marker_symbol
        ;
        ''',
        (components.measurement, components.analysis),
    )
    rows = cursor.fetchall()
    return [
        CellFractionsAverage(**dict(zip(
            ['marker_symbol', 'multiplicity', 'stratum_identifier', 'average_percent'],
            row,
        )))
        for row in rows
    ]


def _get_fractions_test_results(cursor, study: str) -> list[FeatureAssociationTest]:
    derivation_method = describe_fractions_feature_derivation_method()
    cursor.execute('''
    SELECT
        t.selection_criterion_1,
        t.selection_criterion_2,
        t.p_value,
        fs.specifier
    FROM two_cohort_feature_association_test t
    JOIN feature_specification fsn ON fsn.identifier=t.feature_tested
    JOIN feature_specifier fs ON fs.feature_specification=fsn.identifier
    JOIN study_component sc ON sc.component_study=fsn.study
    WHERE fsn.derivation_method=%s
        AND sc.primary_study=%s
        AND t.test=%s
    ;
    ''', (derivation_method, study, 't-test'))
    rows = cursor.fetchall()
    rows = _replace_stratum_identifiers(rows, study, column_index=0)
    rows = _replace_stratum_identifiers(rows, study, column_index=1)
    return [
        FeatureAssociationTest(feature=row[3], cohort1=row[0], cohort2=row[1], pvalue=row[2])
        for row in rows
    ]


def _get_feature_associations(
        tests: list[FeatureAssociationTest],
        pvalue: float,
        cohort_identifiers: list[str],
        features: list[str],
    ) -> dict[str, dict[str, set[str]]]:
    associations: dict[str, dict[str, set[str]]] = {
        feature: {identifier: set() for identifier in cohort_identifiers}
        for feature in features
    }
    for test in tests:
        if float(test.pvalue) <= float(pvalue):
            associations[test.feature][test.cohort1].add(test.cohort2)
            associations[test.feature][test.cohort2].add(test.cohort1)
    return associations


def _create_cell_fractions_summary(
        fractions: list[CellFractionsAverage],
        associations: dict[str, dict[str, set[str]]],
    ) -> list[CellFractionsSummary]:
    return [
        CellFractionsSummary(
            phenotype=f.marker_symbol,
            sample_cohort=f.stratum_identifier,
            significantly_different_cohorts=list(
                associations[f.marker_symbol][f.stratum_identifier]
            ),
            average_percent=f.average_percent,
        )
        for f in fractions
    ]
