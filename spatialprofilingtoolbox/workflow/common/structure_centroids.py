"""An object for storage of summarized-location data for all cells of each study."""
import pickle
from typing import cast
from pickle import dump
from pickle import load
from os.path import join
from os import listdir
from re import search

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)

SpecimenStructureCentroids = dict[int, tuple[float, float]]
StudyStructureCentroids = dict[str, SpecimenStructureCentroids]


class StructureCentroids:
    """An object for storage of summarized-location data for all cells of each study."""
    _studies: dict[str, StudyStructureCentroids]

    def __init__(self, database_config_file: str | None ):
        self._studies = {}
        self.database_config_file = database_config_file

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


    def wrap_up_specimen(self) -> None:
        if len(self._studies) != 1:
            message = 'Need to write exactly 1 specimen at a time, but more or fewer than 1 study are present in buffer: %s'
            raise ValueError(message % list(self._studies.keys()))
        study_name, data = list(self._studies.items())[0]
        specimens = sorted(list(data.keys()))
        if len(specimens) != 1:
            message = 'Need to write exactly 1 specimen at a time, but more or fewer than 1 are present: %s'
            raise ValueError(message % specimens)
        specimen = specimens[0]

        with DBCursor(database_config_file=self.database_config_file, study=study_name) as cursor:
            insert_query = '''
                INSERT INTO
                ondemand_studies_index (
                    specimen,
                    blob_type,
                    blob_contents)
                VALUES (%s, %s, %s) ;
                '''
            cursor.execute(insert_query, (specimen, 'centroids', pickle.dumps(data)))

        message = 'Deleting specimen data "%s" from internal memory, since it is saved to database.'
        logger.debug(message, specimen)
        del self._studies[study_name]
        assert len(self._studies) == 0


    def load_from_db(self) -> None:
        """
        Reads the structure centroids from database
        """
        with DBCursor(database_config_file=self.database_config_file) as cursor:
            cursor.execute('''
                    SELECT study_name FROM study_lookup
                    ''')
            studies = tuple(cursor.fetchall())

        for study in studies:
            with DBCursor(database_config_file=self.database_config_file, study=study) as cursor:
                cursor.execute('''
                        SELECT specimen, blob_contents FROM ondemand_studies_index osi
                        WHERE osi.study_name=%s AND osi.blob_type='centroids';
                        ''', (study, ))
                specimens_to_blobs = tuple(cursor.fetchall())

                self._studies[study] = {}
                for key, value in specimens_to_blobs:
                    if not key in self._studies:
                        self._studies[study][key] = {}
                    self._studies[study][key].update(value)


    def already_exists(self) -> bool:
        with DBCursor(database_config_file=self.database_config_file) as cursor:
            cursor.execute('''
                    SELECT study_name FROM study_lookup
                    ''')
            studies = tuple(cursor.fetchall())

        for study in studies:
            with DBCursor(database_config_file=self.database_config_file, study=study) as cursor:
                cursor.execute('''
                        SELECT COUNT(*) FROM ondemand_studies_index osi
                        WHERE osi.blob_type='centroids';
                        ''')
                count = tuple(cursor.fetchall())[0][0]
                logger.info('Centroids %s found in db ', count)
                return count > 0
