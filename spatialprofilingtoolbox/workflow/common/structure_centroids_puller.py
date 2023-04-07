"""Retrieves positional information for all cells in the SPT database."""
import statistics

from spatialprofilingtoolbox.db.shapefile_polygon import extract_points
from spatialprofilingtoolbox.workflow.common.structure_centroids import StructureCentroids
from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class StructureCentroidsPuller(DatabaseConnectionMaker):
    """Retrieve positional information for all cells in single cell database."""
    def __init__(self, database_config_file):
        super().__init__(database_config_file=database_config_file)
        self.structure_centroids = StructureCentroids()

    def pull(self, specimen: str=None, study: str=None):
        study_names = self.get_study_names(study=study)
        cursor = self.get_connection().cursor()
        for study_name in study_names:
            if specimen is None:
                cursor.execute(self.get_shapefiles_query(), (study_name,))
            else:
                cursor.execute(self.get_shapefiles_query_specimen_specific(),
                              (study_name, specimen))
            rows = cursor.fetchall()
            if len(rows) == 0:
                continue
            self.structure_centroids.add_study_data(
                study_name,
                self.create_study_data(rows)
            )
        cursor.close()

    def get_shapefiles_query(self):
        return '''
        SELECT
        hsi.histological_structure,
        sdmp.specimen,
        sf.base64_contents
        FROM histological_structure_identification hsi
        JOIN shape_file sf ON sf.identifier=hsi.shape_file
        JOIN data_file df ON hsi.data_source=df.sha256_hash
        JOIN specimen_data_measurement_process sdmp ON sdmp.identifier=df.source_generation_process
        WHERE sdmp.study=%s
        ORDER BY
        sdmp.specimen,
        hsi.histological_structure
        ;
        '''

    def get_shapefiles_query_specimen_specific(self):
        return '''
        SELECT
        hsi.histological_structure,
        sdmp.specimen,
        sf.base64_contents
        FROM histological_structure_identification hsi
        JOIN shape_file sf ON sf.identifier=hsi.shape_file
        JOIN data_file df ON hsi.data_source=df.sha256_hash
        JOIN specimen_data_measurement_process sdmp ON sdmp.identifier=df.source_generation_process
        WHERE sdmp.study=%s AND sdmp.specimen=%s
        ORDER BY
        sdmp.specimen,
        hsi.histological_structure
        ;
        '''

    def get_study_names(self, study=None):
        cursor = self.get_connection().cursor()
        if study is None:
            cursor.execute('SELECT name FROM specimen_measurement_study ;')
            rows = cursor.fetchall()
        else:
            cursor.execute('''
            SELECT sms.name FROM specimen_measurement_study sms
            JOIN study_component sc ON sc.component_study=sms.name
            WHERE sc.primary_study=%s
            ;
            ''', (study,))
            rows = cursor.fetchall()
        return sorted([row[0] for row in rows])

    def create_study_data(self, rows):
        study_data = {}
        field = {'structure': 0, 'specimen': 1, 'base64_contents': 2}
        current_specimen = rows[0][field['specimen']]
        specimen_centroids = []
        for row in rows:
            if current_specimen != row[field['specimen']]:
                study_data[current_specimen] = specimen_centroids
                logger.debug('Done parsing shapefiles for specimen "%s".', current_specimen)
                current_specimen = row[field['specimen']]
                specimen_centroids = []
            specimen_centroids.append(self.compute_centroid(
                extract_points(row[field['base64_contents']])
            ))
        study_data[current_specimen] = specimen_centroids
        logger.debug('Done parsing shapefiles for specimen "%s".', current_specimen)
        return study_data

    def compute_centroid(self, points):
        nonrepeating_points = points[0:(len(points)-1)]
        return (
            statistics.mean([point[0] for point in nonrepeating_points]),
            statistics.mean([point[1] for point in nonrepeating_points]),
        )

    def get_structure_centroids(self):
        return self.structure_centroids
