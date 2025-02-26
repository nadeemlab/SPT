"""Common access to a query for specimens."""

from spatialprofilingtoolbox.db.database_connection import DBCursor

def relevant_specimens_query():
    return '''
        SELECT DISTINCT sdmp.specimen FROM specimen_data_measurement_process sdmp
        JOIN study_component sc1 ON sc1.component_study=sdmp.study
        JOIN study_component sc2 ON sc1.primary_study=sc2.primary_study
        JOIN feature_specification fsn ON fsn.study=sc2.component_study
        WHERE fsn.identifier=%s
    '''

def retrieve_cells_selected(study: str, specification: str) -> tuple[int, ...]:
    with DBCursor(study=study) as cursor:
        query = 'SELECT histological_structure FROM cell_set_cache WHERE feature=%s ;'
        cursor.execute(query, (specification,))
        rows = tuple(cursor.fetchall())
    if len(rows) == 0:
        return ()
    return tuple(map(lambda row: int(row[0]), rows))
