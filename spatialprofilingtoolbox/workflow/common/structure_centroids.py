"""An object for storage of summarized-location data for all cells of each study."""

from typing import cast
from pickle import dump
from pickle import load
from os.path import join
from os import listdir
from re import search

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)

SpecimenStructureCentroids = dict[int, tuple[float, float]]
StudyStructureCentroids = dict[str, SpecimenStructureCentroids]


class StructureCentroids:
    """An object for storage of summarized-location data for all cells of each study."""
    _studies: dict[str, StudyStructureCentroids]
    data_directory: str | None

    def __init__(self):
        self._studies = {}
        self.data_directory = None

    def set_data_directory(self, data_directory: str):
        self.data_directory = data_directory

    def get_data_directory(self) -> str:
        return cast(str, self.data_directory)

    def data_directory_available(self) -> bool:
        return self.data_directory is not None

    def get_studies(self) -> dict[str, StudyStructureCentroids]:
        """Retrieve the dictionary of studies.
        
        Returns
        -------
        A dictionary, indexed by study name. For each study, the value is a dictionary providing for
        each specimen name (for specimens collected as part of the given study) the list of pairs of
        pixel coordinate values representing the centroid of the shape specification for a given
        cell. The order is ascending lexicographical order of the corresponding "histological
        structure" identifier strings.
        """
        return self._studies

    def add_study_data(
        self,
        measurement_study: str,
        structure_centroids_by_specimen: StudyStructureCentroids,
    ) -> None:
        """
        Add the study with these structure centroids indexed by specimen to the collection.
        """
        self._studies[measurement_study] = structure_centroids_by_specimen

    def _get_all_centroids_pickle_indices(self) -> tuple[tuple[int, int], ...]:
        def extract_index(filename) -> tuple[int, int]:
            pattern = r'^centroids.(\d+)\.(\d+)\.pickle$'
            match = search(pattern, filename)
            if match is not None:
                return (int(match.groups()[0]), int(match.groups()[1]))
            return cast(tuple[int, int], None)
        filenames = listdir(self.get_data_directory())
        return tuple(set(map(extract_index, filenames)).difference([None]))

    def _form_filename(self, study_index: int, specimen_index: int) -> str:
        return f'centroids.{study_index}.{specimen_index}.pickle'

    def get_all_centroids_pickle_files(self, verbose: bool = False) -> tuple[str, ...]:
        if verbose:
            logger.debug('Checking among files: %s', listdir(self.get_data_directory()))
        return tuple(
            self._form_filename(study_index, specimen_index)
            for study_index, specimen_index in self._get_all_centroids_pickle_indices()
        )

    def wrap_up_specimen(self, study_index: int, specimen_index: int) -> None:
        if not self.data_directory_available():
            return
        if len(self._studies) != 1:
            message = 'Need to write exactly 1 specimen at a time, but more or fewer than 1 study are present in buffer: %s'
            raise ValueError(message % list(self._studies.keys()))
        study_name, data = list(self._studies.items())[0]
        specimens = sorted(list(data.keys()))
        if len(specimens) != 1:
            message = 'Need to write exactly 1 specimen at a time, but more or fewer than 1 are present: %s'
            raise ValueError(message % specimens)
        specimen = specimens[0]
        filename = self._form_filename(study_index, specimen_index)
        self._write_centroids(self._studies, filename)
        message = 'Deleting specimen data "%s" from internal memory, since it is saved to file.'
        logger.debug(message, specimen)
        del self._studies[study_name]
        assert len(self._studies) == 0

    def _write_centroids(self, data: dict[str, StudyStructureCentroids], filename: str) -> None:
        with open(join(self.get_data_directory(), filename), 'wb') as file:
            dump(data, file)

    def load_from_file(self) -> None:
        """
        Reads the structure centroids from files in the data directory supplied during
        initialization.
        """
        for filename in self.get_all_centroids_pickle_files():
            with open(join(self.get_data_directory(), filename), 'rb') as file:
                for key, value in load(file).items():
                    if not key in self._studies:
                        self._studies[key] = {}
                    self._studies[key].update(value)

    @staticmethod
    def already_exists(data_directory: str, verbose: bool = False) -> bool:
        """Checks whether the structure centroids files already exist in the given directory."""
        obj = StructureCentroids()
        obj.set_data_directory(data_directory)
        files = obj.get_all_centroids_pickle_files(verbose=verbose)
        if verbose:
            logger.info('Centroids files found: %s', files)
        if not files:
            return False
        return True
