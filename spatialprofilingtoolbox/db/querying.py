"""Some basic accessors that retrieve from the database."""
import re
from typing import cast

from spatialprofilingtoolbox.workflow.common.export_features import ADIFeatureSpecificationUploader
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudyComponents
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudyHandle
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudyContact
from spatialprofilingtoolbox.db.exchange_data_formats.study import DataRelease
from spatialprofilingtoolbox.db.exchange_data_formats.study import Publication
from spatialprofilingtoolbox.db.exchange_data_formats.study import Institution
from spatialprofilingtoolbox.db.exchange_data_formats.study import Assay
from spatialprofilingtoolbox.db.exchange_data_formats.study import CountsSummary
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudySummary
from spatialprofilingtoolbox.db.exchange_data_formats.study import Context
from spatialprofilingtoolbox.db.exchange_data_formats.study import Products
from spatialprofilingtoolbox.db.exchange_data_formats.study import SampleCohorts
from spatialprofilingtoolbox.db.exchange_data_formats.study import Cohort
from spatialprofilingtoolbox.db.exchange_data_formats.study import CohortAssignment
from spatialprofilingtoolbox.db.simple_query_patterns import get_single_result_row
from spatialprofilingtoolbox.db.simple_query_patterns import get_single_int_result_or_else
from spatialprofilingtoolbox.db.simple_query_patterns import get_single_str_result_or_else


def get_study_components(study_name: str) -> StudyComponents:
    with DBCursor() as cursor:
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
            name = [row[0] for row in cursor.fetchall() if not is_secondary_substudy(row[0])][0]
            substudies[key] = name
    return StudyComponents(**substudies)


def is_secondary_substudy(substudy: str) -> bool:
    is_fractions = bool(re.search('phenotype fractions', substudy))
    is_proximity_calculation = bool(re.search('proximity calculation', substudy))
    descriptor = ADIFeatureSpecificationUploader.ondemand_descriptor()
    is_ondemand_calculation = bool(re.search(descriptor, substudy))
    return is_fractions or is_proximity_calculation or is_ondemand_calculation


def retrieve_study_handles() -> list[StudyHandle]:
    handles: list[StudyHandle] = []
    with DBCursor() as cursor:
        cursor.execute('SELECT study_specifier FROM study;')
        rows = cursor.fetchall()
        for row in rows:
            handle = str(row[0])
            display_name_detail = get_publication_summary_text(cursor, handle)
            handles.append(StudyHandle(handle=handle, display_name_detail=display_name_detail))
    return handles


def get_publication_summary_text(cursor, study: str) -> str:
    query = '''
    SELECT publisher, date_of_publication
    FROM publication
    WHERE study=%s AND document_type=\'Article\'
    ;
    '''
    row = get_single_result_row(cursor, query=query, parameters=(study,),)
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


def get_contact(cursor, study: str) -> StudyContact:
    row = get_single_result_row(
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
        email_address=row[1] if rough_check_is_email(row[1]) else None
    )


def rough_check_is_email(string):
    return not re.match('^[A-Za-z0-9+_.-]+@([^ ]+)$', string) is None


def get_data_release(cursor, study: str) -> DataRelease:
    query = '''
    SELECT publisher, internet_reference, date_of_publication
    FROM publication
    WHERE study=%s AND document_type=\'Dataset\'
    ;
    '''
    row = get_single_result_row(cursor, query=query, parameters=(study,),)
    row = cast(tuple, row)
    return DataRelease(**dict(zip(['repository', 'url', 'date'], row)))


def get_publication(cursor, study: str) -> Publication | None:
    query = '''
    SELECT title, internet_reference, date_of_publication
    FROM publication
    WHERE study=%s AND document_type=\'Article\'
    ;
    '''
    row = get_single_result_row(cursor, query=query, parameters=(study,),)
    if row is None:
        return None
    title, url, date = row
    first_author_name = get_single_str_result_or_else(
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


def get_assay(cursor, measurement_study: str) -> Assay:
    name = get_single_str_result_or_else(
        cursor,
        query='SELECT assay FROM specimen_measurement_study WHERE name=%s;',
        parameters=(measurement_study,),
    )
    return Assay(name=name)


def get_number_cells(cursor, specimen_measurement_study: str) -> int:
    query = '''
    SELECT count(*)
    FROM histological_structure_identification hsi
    JOIN histological_structure hs ON hsi.histological_structure = hs.identifier
    JOIN data_file df ON hsi.data_source = df.sha256_hash
    JOIN specimen_data_measurement_process sdmp ON df.source_generation_process = sdmp.identifier
    WHERE sdmp.study=%s AND hs.anatomical_entity='cell'
    ;
    '''
    return get_single_int_result_or_else(
        cursor,
        query=query,
        parameters=(specimen_measurement_study,),
    )


def get_number_channels(cursor, specimen_measurement_study: str) -> int:
    query = '''
    SELECT count(*)
    FROM biological_marking_system bms
    WHERE bms.study=%s
    ;
    '''
    return get_single_int_result_or_else(
        cursor,
        query=query,
        parameters=(specimen_measurement_study,),
    )


def get_number_specimens(cursor, specimen_measurement_study: str) -> int:
    return get_single_int_result_or_else(
        cursor,
        query='''
        SELECT count(DISTINCT specimen)
        FROM specimen_data_measurement_process
        WHERE study=%s
        ;
        ''',
        parameters=(specimen_measurement_study,),
    )

def get_number_composite_phenotypes(cursor, analysis_study: str) -> int:
    return get_single_int_result_or_else(
        cursor,
        query='''
        SELECT count(DISTINCT cell_phenotype)
        FROM cell_phenotype_criterion
        WHERE study=%s
        ;
        ''',
        parameters=(analysis_study,),
    )


def get_counts_summary(study: str) -> CountsSummary:
    components = get_study_components(study)
    with DBCursor() as cursor:
        summary = CountsSummary(
            specimens=get_number_specimens(cursor, components.measurement),
            cells=get_number_cells(cursor, components.measurement),
            channels=get_number_channels(cursor, components.measurement),
            composite_phenotypes=get_number_composite_phenotypes(cursor, components.analysis),
        )
    return summary


def get_institution(study: str) -> Institution:
    with DBCursor() as cursor:
        name = get_single_str_result_or_else(
            cursor,
            query='SELECT institution FROM study WHERE study_specifier=%s; ',
            parameters=(study,),
        )
    return Institution(name=name)


def get_study_summary(study: str) -> StudySummary:
    components = get_study_components(study)
    counts_summary = get_counts_summary(study)
    institution = get_institution(study)

    with DBCursor() as cursor:
        contact = get_contact(cursor, study)
        data_release = get_data_release(cursor, study)
        publication = get_publication(cursor, study)
        assay = get_assay(cursor, components.measurement)
        sample_cohorts = get_sample_cohorts(cursor, components.collection)

    return StudySummary(
        context=Context(institution=institution, assay=assay, contact=contact),
        products=Products(data_release=data_release, publication=publication),
        counts=counts_summary,
        cohorts=sample_cohorts,
    )


def get_sample_cohorts(cursor, specimen_collection_study: str) -> SampleCohorts:
    decrement, cohorts = get_cohorts_list(cursor, specimen_collection_study)
    assignments = get_cohort_assignments(cursor, specimen_collection_study, decrement)
    return SampleCohorts(assignments=assignments, cohorts=cohorts)


def get_cohorts_list(cursor, specimen_collection_study: str) -> tuple[int, list[Cohort]]:
    query = '''
    SELECT DISTINCT
        sst.stratum_identifier,
        sst.local_temporal_position_indicator,
        sst.subject_diagnosed_condition,
        sst.subject_diagnosed_result
    FROM sample_strata sst
    JOIN specimen_collection_process scp
    ON scp.specimen = sst.sample
    WHERE scp.study=%s ;
    '''
    cursor.execute(query, (specimen_collection_study,))
    sample_cohorts = cursor.fetchall()
    if len(sample_cohorts) == 0:
        return 0, []
    decrement = min((int(row[0]) for row in sample_cohorts)) - 1
    sample_cohorts_decremented = [
        Cohort(**dict(zip(
            ['identifier', 'temporality', 'diagnosis', 'result'],
            [str(int(row[0]) - decrement), row[1], row[2], row[3]],
        )))
        for row in sample_cohorts
    ]
    return decrement, sorted(sample_cohorts_decremented, key=lambda x: int(x[0]))


def get_cohort_assignments(
        cursor,
        specimen_collection_study: str,
        decrement: int
    ) -> list[CohortAssignment]:
    query = '''
    SELECT sst.sample, sst.stratum_identifier
    FROM sample_strata sst
    JOIN specimen_collection_process scp
    ON scp.specimen = sst.sample
    WHERE scp.study=%s
    ORDER BY sample ;
    '''
    cursor.execute(query, (specimen_collection_study,))
    rows = cursor.fetchall()
    cohort_identifier = { row[0] : row[1] for row in rows }
    query = '''
    SELECT scp.specimen, COUNT(*)
    FROM specimen_collection_process scp
    JOIN specimen_data_measurement_process sdmp
    ON scp.specimen=sdmp.specimen
    JOIN data_file df
    ON df.source_generation_process=sdmp.identifier
    JOIN histological_structure_identification hsi
    ON hsi.data_source=df.sha256_hash
    WHERE scp.study=%s
    GROUP BY scp.specimen ;
    '''
    cursor.execute(query, (specimen_collection_study,))
    rows = cursor.fetchall()
    cell_count: dict[str, int] = { row[0] : row[1] for row in rows }
    return [
        CohortAssignment(sample=sample, cohort=str(int(cohort_identifier[sample]) - decrement))
        for sample in sorted(list(set(cell_count.keys()).intersection(cohort_identifier.keys())))
    ]
