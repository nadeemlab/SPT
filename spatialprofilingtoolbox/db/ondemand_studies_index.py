"""Count number of cached files of given types in cached-files area of database."""

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import retrieve_study_names

def get_counts(database_config_file: str, blob_type: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for study in retrieve_study_names(database_config_file):
        with DBCursor(database_config_file=database_config_file, study=study) as cursor:
            cursor.execute(f'''
                SELECT COUNT(*) FROM ondemand_studies_index osi
                WHERE osi.blob_type='{blob_type}' ;
            ''')
            count = tuple(cursor.fetchall())[0][0]
            counts[study] = count
    return counts


def drop_cache_files(database_config_file: str, blob_type: str) -> None:
    for study in retrieve_study_names(database_config_file):
        with DBCursor(database_config_file=database_config_file, study=study) as cursor:
            cursor.execute(f'''
                DELETE FROM ondemand_studies_index osi
                WHERE osi.blob_type='{blob_type}' ;
            ''')


def retrieve_expressions_index(database_config_file: str, study: str) -> str:
    with DBCursor(database_config_file=database_config_file, study=study) as cursor:
        cursor.execute('''
            SELECT blob_contents FROM ondemand_studies_index osi
            WHERE osi.blob_type='expressions_index' ;
        ''')
        result_blob = bytearray(tuple(cursor.fetchall())[0][0])
    return result_blob.decode(encoding='utf-8')
