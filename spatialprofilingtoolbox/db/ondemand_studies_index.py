"""Count number of cached files of given types in cached-files area of database."""

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import retrieve_study_names

def get_counts(database_config_file: str, blob_type: str, study: str | None = None) -> dict[str, int]:
    if study is None:
        studies = tuple(retrieve_study_names(database_config_file))
    else:
        studies = (study,)
    counts: dict[str, int] = {}
    for study in studies:
        with DBCursor(database_config_file=database_config_file, study=study) as cursor:
            cursor.execute(f'''
                SELECT COUNT(*) FROM ondemand_studies_index osi
                WHERE osi.blob_type='{blob_type}' ;
            ''')
            count = tuple(cursor.fetchall())[0][0]
            counts[study] = count
    return counts


def drop_cache_files(database_config_file: str, blob_type: str, study: str | None = None) -> None:
    if study is None:
        studies = tuple(retrieve_study_names(database_config_file))
    else:
        studies = (study,)
    for _study in studies:
        with DBCursor(database_config_file=database_config_file, study=_study) as cursor:
            cursor.execute(f'''
                DELETE FROM ondemand_studies_index osi
                WHERE osi.blob_type='{blob_type}' ;
            ''')


def retrieve_expressions_index(database_config_file: str, study: str) -> str | None:
    with DBCursor(database_config_file=database_config_file, study=study) as cursor:
        cursor.execute('''
            SELECT blob_contents FROM ondemand_studies_index osi
            WHERE osi.blob_type='expressions_index' ;
        ''')
        rows = tuple(cursor.fetchall())
        if len(rows) == 0:
            return None
        result_blob = bytearray(rows[0][0])
    return result_blob.decode(encoding='utf-8')


def retrieve_indexed_samples(database_config_file: str, study: str) -> tuple[str, ...]:
    with DBCursor(database_config_file=database_config_file, study=study) as cursor:
        cursor.execute('''
            SELECT specimen FROM ondemand_studies_index osi
            WHERE osi.blob_type='feature_matrix' ;
        ''')
        specimens = tuple(r[0] for r in cursor.fetchall())
    return specimens
