"""Retrieves positional information for all cells in the SPT database."""

from statistics import mean
from typing import Any
from typing import cast

from psycopg2.extensions import cursor as Psycopg2Cursor

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.shapefile_polygon import extract_points
from spatialprofilingtoolbox.workflow.common.structure_centroids import (
    StructureCentroids,
    StudyStructureCentroids,
)
from spatialprofilingtoolbox.workflow.common.logging.fractional_progress_reporter \
    import FractionalProgressReporter
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class StructureCentroidsPuller:
    """Retrieve positional information for all cells in single cell database."""

    database_config_file: str | None
    _structure_centroids: StructureCentroids

    def __init__(self, database_config_file: str | None):
        self.database_config_file = database_config_file
        self._structure_centroids = StructureCentroids()

    def pull_and_write_to_files(self, data_directory: str):
        self.get_structure_centroids().set_data_directory(data_directory)
        study_names = self._get_study_names()
        for study_index, (study_name, measurement_study) in enumerate(study_names):
            specimens = self._get_specimens(study_name, measurement_study)
            progress_reporter = FractionalProgressReporter(
                len(specimens),
                parts=8,
                task_and_done_message=(f'pulling centroids for study "{study_name}"', None),
                logger=logger,
            )
            for specimen_index, specimen in enumerate(specimens):
                self.pull(specimen=specimen)
                self.get_structure_centroids().wrap_up_specimen(study_index, specimen_index)
                progress_reporter.increment(iteration_details=specimen)
            progress_reporter.done()

    def pull(
        self,
        specimen: str | None = None,
        study: str | None = None,
        histological_structures: set[int] | None = None,
    ) -> None:
        """Pull centroids into self.structure_centroids.

        Parameters
        ----------
        specimen: str | None = None
        study: str | None = None
            Which specimen to extract features for or study to extract features for all specimens
            for. Exactly one of specimen or study must be provided.
        histological_structures: set[int] | None = None
            Which histological structures to extract features for from the given study or specimen,
            by their histological structure ID. Structures not found in either the provided
            specimen or study are ignored.
            If None, all structures are fetched.
        """
        study_names = self._get_study_names(study=study)
        for study_name, measurement_study in study_names:
            parameters: list[str | tuple[str, ...]] = [measurement_study]

            with DBCursor(database_config_file=self.database_config_file, study=study_name) as cursor:
                if specimen is not None:
                    parameters.append(specimen)
                    specimen_count = 1
                else:
                    specimen_count = self._get_specimen_count(measurement_study, cursor)
                if histological_structures is not None:
                    parameters.append(tuple(str(hs_id) for hs_id in histological_structures))

                cursor.execute(
                    self._get_shapefiles_query(
                        specimen is not None,
                        histological_structures is not None,
                    ),
                    parameters,
                )

                rows: list = []
                total = cursor.rowcount
                while cursor.rownumber < total - 1:
                    current_number_stored = len(rows)
                    rows.extend(cursor.fetchmany(size=self._get_batch_size()))
                    received = len(rows) - current_number_stored
                    logger.debug('Received %s shapefiles entries from DB.', received)
            if len(rows) == 0:
                continue

            self._structure_centroids.add_study_data(
                measurement_study,
                self._create_study_data(rows, specimen_count, study_name)
            )

    def _get_batch_size(self) -> int:
        return pow(10, 5)

    def _get_specimen_count(self,
        measurement_study: str,
        cursor: Psycopg2Cursor,
    ) -> int:
        cursor.execute('''
        SELECT COUNT(*) FROM specimen_data_measurement_process sdmp
        WHERE sdmp.study=%s ;
        ''', (measurement_study,))
        return cursor.fetchall()[0][0]

    @staticmethod
    def _get_shapefiles_query(
        specimen_specific: bool = False,
        histological_structures_condition: bool = False,
    ) -> str:
        return f'''
        SELECT
            hsi.histological_structure,
            sdmp.specimen,
            sf.base64_contents
        FROM histological_structure_identification hsi
            JOIN shape_file sf
                ON sf.identifier=hsi.shape_file
            JOIN data_file df
                ON hsi.data_source=df.sha256_hash
            JOIN specimen_data_measurement_process sdmp
                ON sdmp.identifier=df.source_generation_process
        WHERE sdmp.study=%s
            {'AND sdmp.specimen=%s' if specimen_specific else ''}
            {'AND hsi.histological_structure IN %s' if histological_structures_condition else ''}
        ORDER BY
            sdmp.specimen,
            hsi.histological_structure
        ;
        '''

    def _get_specimen_measurement_study(self, study: str) -> str:
        with DBCursor(database_config_file=self.database_config_file, study=study) as cursor:
            cursor.execute('''
            SELECT sms.name FROM specimen_measurement_study sms
            JOIN study_component sc ON sc.component_study=sms.name
            WHERE sc.primary_study=%s
            ;
            ''', (study,))
            rows = cursor.fetchall()
        return rows[0][0]

    def _get_study_names(self, study: str | None = None) -> list[tuple[str, str]]:
        if study is None:
            with DBCursor(database_config_file=self.database_config_file) as cursor:
                cursor.execute('SELECT study FROM study_lookup ;')
                rows = cursor.fetchall()
            studies = [(study, self._get_specimen_measurement_study(study)) for (study,) in rows]
        else:
            studies = [(study, self._get_specimen_measurement_study(study))]
        return sorted(studies, key=lambda x: x[1])

    def _create_study_data(
        self,
        rows: list[tuple[Any, ...]],
        specimen_count: int,
        study: str,
    ) -> StudyStructureCentroids:
        study_data: StudyStructureCentroids = {}
        field = {'structure': 0, 'specimen': 1, 'base64_contents': 2}
        current_specimen = rows[0][field['specimen']]
        specimen_centroids: dict[int, tuple[float, float]] = {}
        for row in rows:
            if current_specimen != row[field['specimen']]:
                study_data[current_specimen] = specimen_centroids
                current_specimen = row[field['specimen']]
                specimen_centroids = {}
            specimen_centroids[int(row[field['structure']])] = self._compute_centroid(
                extract_points(row[field['base64_contents']])
            )
        study_data[current_specimen] = specimen_centroids
        return study_data

    def _get_specimens(self, study_name: str, measurement_study: str) -> tuple[str, ...]:
        with DBCursor(database_config_file=self.database_config_file, study=study_name) as cursor:
            cursor.execute('''
            SELECT sdmp.specimen
            FROM specimen_data_measurement_process sdmp
            WHERE sdmp.study=%s
            ORDER BY sdmp.specimen
            ;
            ''', (measurement_study,))
            rows = cursor.fetchall()
        return tuple(sorted([cast(str, row[0]) for row in rows]))

    def _compute_centroid(self, points: list[tuple[float, float]]) -> tuple[float, float]:
        nonrepeating_points = points[0:(len(points)-1)]
        return (
            mean([point[0] for point in nonrepeating_points]),
            mean([point[1] for point in nonrepeating_points]),
        )

    def get_structure_centroids(self) -> StructureCentroids:
        return self._structure_centroids
