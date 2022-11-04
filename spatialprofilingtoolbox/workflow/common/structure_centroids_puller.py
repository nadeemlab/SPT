
from ...standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)

from ...db.database_connection import DatabaseConnectionMaker


class StructureCentroids:
    """
    An object for in-memory storage of summarized-location data for all cells of
    each study

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
        self.structure_centroids = None

    def pull(self):
        self.structure_centroids = 'x'

    def get_structure_centroids(self):
        return self.structure_centroids
