"""Convenience accessors of study-related small data / metadata."""
from typing import cast
import re

from spatialprofilingtoolbox.workflow.common.export_features import ADIFeatureSpecificationUploader
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudyContact
from spatialprofilingtoolbox.db.exchange_data_formats.study import DataRelease
from spatialprofilingtoolbox.db.exchange_data_formats.study import Publication
from spatialprofilingtoolbox.db.exchange_data_formats.study import Institution
from spatialprofilingtoolbox.db.exchange_data_formats.study import Assay
from spatialprofilingtoolbox.db.exchange_data_formats.study import CountsSummary
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudyComponents
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudyHandle
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudySummary
from spatialprofilingtoolbox.db.exchange_data_formats.study import Context
from spatialprofilingtoolbox.db.exchange_data_formats.study import Products
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeSymbol
from spatialprofilingtoolbox.db.simple_query_patterns import GetSingleResult
from spatialprofilingtoolbox.db.cohorts import _get_sample_cohorts


def _get_study_summary(cursor, study: str) -> StudySummary:
    components = _get_study_components(cursor, study)
    counts_summary = _get_counts_summary(cursor, components)
    contact = _get_contact(cursor, study)
    institution = _get_institution(cursor, study)
    data_release = _get_data_release(cursor, study)
    publication = _get_publication(cursor, study)
    assay = _get_assay(cursor, components.measurement)
    sample_cohorts = _get_sample_cohorts(cursor, study)

    return StudySummary(
        context=Context(institution=institution, assay=assay, contact=contact),
        products=Products(data_release=data_release, publication=publication),
        counts=counts_summary,
        cohorts=sample_cohorts,
    )


def _get_study_components(cursor, study_name: str) -> StudyComponents:
    substudy_tables = {
        'collection': 'specimen_collection_study',
        'measurement': 'specimen_measurement_study',
        'analysis': 'data_analysis_study',
    }
    substudies = {}
    for key, tablename in substudy_tables.items():
        cursor.execute(f'''
        SELECT ss.name FROM {tablename} ss
        JOIN study_component sc ON sc.component_study=ss.name
        WHERE sc.primary_study=%s
        ;
        ''', (study_name,))
        name = [row[0] for row in cursor.fetchall() if not _is_secondary_substudy(row[0])][0]
        substudies[key] = name
    return StudyComponents(**substudies)


def _is_secondary_substudy(substudy: str) -> bool:
    is_fractions = bool(re.search('phenotype fractions', substudy))
    is_proximity_calculation = bool(re.search('proximity calculation', substudy))
    descriptor = ADIFeatureSpecificationUploader.ondemand_descriptor()
    is_ondemand_calculation = bool(re.search(descriptor, substudy))
    return is_fractions or is_proximity_calculation or is_ondemand_calculation


def _get_study_handles(cursor) -> list[StudyHandle]:
    handles: list[StudyHandle] = []
    cursor.execute('SELECT study_specifier FROM study;')
    rows = cursor.fetchall()
    for row in rows:
        handle = str(row[0])
        display_name_detail = _get_publication_summary_text(cursor, handle)
        handles.append(StudyHandle(handle=handle, display_name_detail=display_name_detail))
    return handles


def _get_publication_summary_text(cursor, study: str) -> str:
    query = '''
    SELECT publisher, date_of_publication
    FROM publication
    WHERE study=%s AND document_type=\'Article\'
    ;
    '''
    row = GetSingleResult.row(cursor, query=query, parameters=(study,),)
    if row is None:
        publication_summary_text = ''
    else:
        publisher, publication_date = row
        year_match = re.search(r'^\d{4}', publication_date)
        if year_match:
            year = year_match.group()
            publication_summary_text = f'{publisher} {year}'
        else:
            publication_summary_text = publisher
    return publication_summary_text


def _get_contact(cursor, study: str) -> StudyContact:
    row = GetSingleResult.row(
        cursor,
        query='''
        SELECT name, contact_reference
        FROM study_contact_person
        WHERE study=%s
        ''',
        parameters=(study,),
    )
    row = cast(tuple, row)
    return StudyContact(
        name=row[0],
        email_address=row[1] if _rough_check_is_email(row[1]) else None
    )


def _rough_check_is_email(string):
    return not re.match('^[A-Za-z0-9+_.-]+@([^ ]+)$', string) is None


def _get_data_release(cursor, study: str) -> DataRelease:
    query = '''
    SELECT publisher, internet_reference, date_of_publication
    FROM publication
    WHERE study=%s AND document_type=\'Dataset\'
    ;
    '''
    row = GetSingleResult.row(cursor, query=query, parameters=(study,),)
    row = cast(tuple, row)
    return DataRelease(**dict(zip(['repository', 'url', 'date'], row)))


def _get_publication(cursor, study: str) -> Publication | None:
    query = '''
    SELECT title, internet_reference, date_of_publication
    FROM publication
    WHERE study=%s AND document_type=\'Article\'
    ;
    '''
    row = GetSingleResult.row(cursor, query=query, parameters=(study,),)
    if row is None:
        return None
    title, url, date = row
    first_author_name = GetSingleResult.string(
        cursor,
        query='''
        SELECT person FROM author
        WHERE publication=%s
        ORDER BY regexp_replace(ordinality, '[^0-9]+', '', 'g')::int
        ;
        ''',
        parameters=(title,),
        or_else_value='',
    )
    return Publication(title=title, url=url, first_author_name=first_author_name, date=date)


def _get_assay(cursor, measurement_study: str) -> Assay:
    name = GetSingleResult.string(
        cursor,
        query='SELECT assay FROM specimen_measurement_study WHERE name=%s;',
        parameters=(measurement_study,),
    )
    return Assay(name=name)


def _get_number_cells(cursor, specimen_measurement_study: str) -> int:
    query = '''
    SELECT count(*)
    FROM histological_structure_identification hsi
    JOIN histological_structure hs ON hsi.histological_structure = hs.identifier
    JOIN data_file df ON hsi.data_source = df.sha256_hash
    JOIN specimen_data_measurement_process sdmp ON df.source_generation_process = sdmp.identifier
    WHERE sdmp.study=%s AND hs.anatomical_entity='cell'
    ;
    '''
    return GetSingleResult.integer(
        cursor,
        query=query,
        parameters=(specimen_measurement_study,),
    )


def _get_number_channels(cursor, specimen_measurement_study: str) -> int:
    query = '''
    SELECT count(*)
    FROM biological_marking_system bms
    WHERE bms.study=%s
    ;
    '''
    return GetSingleResult.integer(
        cursor,
        query=query,
        parameters=(specimen_measurement_study,),
    )


def _get_number_specimens(cursor, specimen_measurement_study: str) -> int:
    return GetSingleResult.integer(
        cursor,
        query='''
        SELECT count(DISTINCT specimen)
        FROM specimen_data_measurement_process
        WHERE study=%s
        ;
        ''',
        parameters=(specimen_measurement_study,),
    )


def _get_number_composite_phenotypes(cursor, analysis_study: str) -> int:
    return GetSingleResult.integer(
        cursor,
        query='''
        SELECT count(DISTINCT cell_phenotype)
        FROM cell_phenotype_criterion
        WHERE study=%s
        ;
        ''',
        parameters=(analysis_study,),
    )


def _get_counts_summary(cursor, components: StudyComponents) -> CountsSummary:
    return CountsSummary(
        specimens=_get_number_specimens(cursor, components.measurement),
        cells=_get_number_cells(cursor, components.measurement),
        channels=_get_number_channels(cursor, components.measurement),
        composite_phenotypes=_get_number_composite_phenotypes(cursor, components.analysis),
    )


def _get_institution(cursor, study: str) -> Institution:
    name = GetSingleResult.string(
        cursor,
        query='SELECT institution FROM study WHERE study_specifier=%s; ',
        parameters=(study,),
    )
    return Institution(name=name)


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
