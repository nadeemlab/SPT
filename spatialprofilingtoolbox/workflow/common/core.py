"""Convenience functions for core jobs."""

from spatialprofilingtoolbox import DatabaseConnectionMaker

def get_number_cells_to_be_processed(database_config_file, study_name, sample_identifier=None):
    query_parts = ['''
    SELECT COUNT(*) FROM
    histological_structure_identification hsi
    JOIN histological_structure hs ON hsi.histological_structure=hs.identifier
    JOIN data_file df ON df.sha256_hash=hsi.data_source
    JOIN specimen_data_measurement_process sdmp ON df.source_generation_process=sdmp.identifier
    JOIN specimen_collection_process scp ON scp.specimen=sdmp.specimen
    JOIN study_component sc ON sc.component_study=scp.study
    WHERE sc.primary_study=%s AND hs.anatomical_entity='cell'
    ''']
    if sample_identifier is not None:
        query_parts.append('AND sdmp.specimen=%s')
        fill_ins = (study_name, sample_identifier)
    else:
        fill_ins = (study_name,)
    query_parts.append(';')
    query = ' '.join(query_parts)
    with DatabaseConnectionMaker(database_config_file) as dcm:
        connection = dcm.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, fill_ins)
        rows = cursor.fetchall()
        cursor.close()
    return rows[0][0]
