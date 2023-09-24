"""An object for in-memory storage of summarized-location data for all cells of each study."""

from pickle import dump
from pickle import load
from os.path import join
from os.path import isfile

from spatialprofilingtoolbox.ondemand.defaults import CENTROIDS_FILENAME

StudyStructureCentroids = dict[str, dict[int, tuple[float, float]]]


class StructureCentroids:
    """An object for in-memory storage of summarized-location data for all cells of each study.

    Member `studies` is a dictionary with keys the study names. The values are dictionaries,
    providing for each specimen name (for specimens collected as part of the given study) the list
    of pairs of pixel coordinate values representing the centroid of the shape specification for a
    given cell. The order is ascending lexicographical order of the corresponding "histological
    structure" identifier strings.
    """

    def __init__(self):
        self._studies: dict[str, StudyStructureCentroids] = {}

    def get_studies(self) -> dict[str, StudyStructureCentroids]:
        return self._studies

    def add_study_data(
        self,
        study_name: str,
        structure_centroids_by_specimen: StudyStructureCentroids,
    ) -> None:
        self._studies[study_name] = structure_centroids_by_specimen

    def write_to_file(self, data_directory: str) -> None:
        with open(join(data_directory, CENTROIDS_FILENAME), 'wb') as file:
            dump(self.get_studies(), file)

    def load_from_file(self, data_directory: str) -> None:
        with open(join(data_directory, CENTROIDS_FILENAME), 'rb') as file:
            self._studies = load(file)

    @staticmethod
    def already_exists(data_directory: str) -> bool:
        return isfile(join(data_directory, CENTROIDS_FILENAME))
