"""Convenience functions for core jobs."""

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker

def get_number_cells_to_be_processed(database_config_file, study_name, sample_identifier):
    with DatabaseConnectionMaker(database_config_file) as dcm:
        connection = dcm.get_connection()
        cursor = connection.cursor()
        cursor.execute('''
        SELECT COUNT(*)
        FROM
        histological_structure_identification hsi
        JOIN histological_structure hs ON hsi.histological_structure=hs.identifier
        JOIN data_file df ON df.sha256_hash=hsi.data_source
        JOIN specimen_data_measurement_process sdmp ON df.source_generation_process=sdmp.identifier
        JOIN specimen_collection_process scp ON scp.specimen=sdmp.specimen
        JOIN study_component sc ON sc.component_study=scp.study
        WHERE sc.primary_study=%s AND sdmp.specimen=%s AND hs.anatomical_entity='cell'
        ;
        ''', (study_name, sample_identifier))
        rows = cursor.fetchall()
        cursor.close()
    return rows[0][0]
