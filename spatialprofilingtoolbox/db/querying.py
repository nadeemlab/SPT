"""Some basic accessors that retrieve from the database."""
import re

from spatialprofilingtoolbox.workflow.common.export_features import ADIFeatureSpecificationUploader
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudyComponents
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudyHandle


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
            display_name = get_publication_summary_text(cursor, handle)
            handles.append(StudyHandle(handle=handle, display_name=display_name))
    return handles


def get_publication_summary_text(cursor, study) -> str:
    query = '''
    SELECT publisher, date_of_publication
    FROM publication
    WHERE study=%s AND document_type=\'Article\'
    ;
    '''
    row = get_single_result_row(cursor, query=query, parameters=(study,),)
    if len(row) == 0:
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


def get_single_result_row(cursor, query, parameters=None):
    if not parameters is None:
        cursor.execute(query, parameters)
    else:
        cursor.execute(query)
    rows = cursor.fetchall()
    if len(rows) > 0:
        return list(rows[0])
    return []
