import statistics

from ...standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)

from ...db.database_connection import DatabaseConnectionMaker
from ...db.shapefile_polygon import extract_points


class StructureCentroids:
    """
    An object for in-memory storage of summarized-location data for all cells of
    each study.

    Member `studies` is a dictionary with keys the study names. The values are
    dictionaries, providing for each specimen name (for specimens collected as 
    part of the given study) the list of pairs of pixel coordinate values
    representing the centroid of the shape specification for a given cell. The
    order is ascending lexicographical order of the corresponding "histological
    structure" identifier strings.
    """
    def __init__(self):
        self.studies = {}

    def add_study_data(self, study_name, structure_centroids_by_specimen):
        self.studies[study_name] = structure_centroids_by_specimen


class StructureCentroidsPuller(DatabaseConnectionMaker):
    def __init__(self, database_config_file):
        super(StructureCentroidsPuller, self).__init__(database_config_file=database_config_file)
        self.structure_centroids = StructureCentroids()

    def pull(self):
        shapefiles_query='''
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
        study_names = self.get_study_names()
        cursor = self.get_connection().cursor()
        for study_name in study_names:
            cursor.execute(shapefiles_query, (study_name,))
            rows = cursor.fetchall()
            self.structure_centroids.add_study_data(
                study_name,
                self.create_study_data(rows)
            )
        cursor.close()

    def get_study_names(self):
        query='''
        SELECT
        sdmp.study
        FROM specimen_data_measurement_process sdmp
        ;
        '''
        cursor = self.get_connection().cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        return sorted([row[0] for row in rows])

    def create_study_data(self, rows):
        study_data = {}
        field = { 'structure' : 0, 'specimen' : 1, 'base64_contents' : 2 }
        current_specimen = rows[0][field['specimen']]
        specimen_centroids = []
        for row in rows:
            if current_specimen != row[field['specimen']]:
                study_data[current_specimen] = specimen_centroids
                current_specimen = row[field['specimen']]
                logger.debug('Done parsing shapefiles for specimen "%s".', current_specimen)
                specimen_centroids = []
            specimen_centroids.append(self.compute_centroid(
                extract_points(row[field['base64_contents']])
            ))
        study_data[current_specimen] = specimen_centroids
        logger.debug('Done parsing shapefiles for specimen "%s".', current_specimen)
        return study_data

    def compute_centroid(self, points):
        nonrepeating_points = points[0:(len(points)-1)]
        return [
            statistics.mean([point[0] for point in nonrepeating_points]),
            statistics.mean([point[1] for point in nonrepeating_points]),
        ]

    def get_structure_centroids(self):
        return self.structure_centroids


