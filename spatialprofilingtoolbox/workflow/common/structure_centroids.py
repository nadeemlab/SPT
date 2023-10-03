"""An object for storage of summarized-location data for all cells of each study."""

from typing import cast
from pickle import dump
from pickle import load
from os.path import join
from os import listdir
from re import search

StudyStructureCentroids = dict[str, dict[int, tuple[float, float]]]


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
        study_name: str,
        structure_centroids_by_specimen: StudyStructureCentroids,
    ) -> None:
        """
        Add the study with these structure centroids indexed by specimen to the collection.
        If a non-trivial data_directory is available, these will be written to file and not stored
        in program memory.
        """
        if self.get_data_directory() is None:
            self._studies[study_name] = structure_centroids_by_specimen
        else:
            filename = self._get_next_centroids_pickle()
            with open(join(self.get_data_directory(), filename), 'wb') as file:
                dump({study_name: structure_centroids_by_specimen}, file)

    def _get_all_centroids_pickle_indices(self) -> tuple[int, ...]:
        def extract_index(filename) -> int:
            pattern = r'^centroids_pickle_(\d+)\.pickle$'
            match = search(pattern, filename)
            if match is not None:
                return int(match.groups()[0])
            return cast(int, None)
        filenames = listdir(self.get_data_directory())
        return tuple(set(map(extract_index, filenames)).difference([None]))

    def _get_next_centroids_pickle(self) -> str:
        indices = self._get_all_centroids_pickle_indices()
        if len(indices) == 0:
            index = 0
        else:
            index = max(indices) + 1
        return self._form_filename(index)

    def _form_filename(self, index: int) -> str:
        return f'centroids_pickle_{index}.pickle'

    def get_all_centroids_pickle_files(self) -> tuple[str, ...]:
        return tuple(
            self._form_filename(index)
            for index in self._get_all_centroids_pickle_indices()
        )

    def load_from_file(self) -> None:
        """
        Reads the structure centroids from files in the data directory supplied during
        initialization.
        """
        for filename in self.get_all_centroids_pickle_files():
            with open(join(self.get_data_directory(), filename), 'rb') as file:
                for key, value in load(file).items():
                    self._studies[key] = value

    @staticmethod
    def already_exists(data_directory: str) -> bool:
        """Checks whether the structure centroids files already exists in the given directory."""
        obj = StructureCentroids()
        obj.set_data_directory(data_directory)
        if not obj.get_all_centroids_pickle_files():
            return False
        return True
