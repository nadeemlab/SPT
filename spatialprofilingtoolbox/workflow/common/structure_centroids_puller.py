"""Retrieves positional information for all cells in the SPT database."""

from statistics import mean
from typing import Any

from psycopg2.extensions import cursor as Psycopg2Cursor

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

    cursor: Psycopg2Cursor
    _structure_centroids: StructureCentroids

    def __init__(self, cursor: Psycopg2Cursor):
        self.cursor = cursor
        self._structure_centroids = StructureCentroids()

    def pull_and_write_to_files(self, data_directory: str):
        self._structure_centroids.set_data_directory(data_directory)
        self.pull()

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
        for study_name in study_names:
            parameters: list[str | tuple[str, ...]] = [study_name]
            if specimen is not None:
                parameters.append(specimen)
                specimen_count = 1
            else:
                specimen_count = self._get_specimen_count(study_name, self.cursor)
            if histological_structures is not None:
                parameters.append(tuple(str(hs_id) for hs_id in histological_structures))

            self.cursor.execute(
                self._get_shapefiles_query(
                    specimen is not None,
                    histological_structures is not None,
                ),
                parameters,
            )

            rows: list = []
            total = self.cursor.rowcount
            while self.cursor.rownumber < total - 1:
                current_number_stored = len(rows)
                rows.extend(self.cursor.fetchmany(size=self._get_batch_size()))
                received = len(rows) - current_number_stored
                logger.debug('Received %s shapefiles entries from DB.', received)
            if len(rows) == 0:
                continue

            self._structure_centroids.add_study_data(
                study_name,
                self._create_study_data(rows, specimen_count, study_name)
            )

    def _get_batch_size(self) -> int:
        return pow(10, 5)

    def _get_specimen_count(self, study_name: str, cursor: Psycopg2Cursor) -> int:
        cursor.execute('''
        SELECT COUNT(*) FROM specimen_data_measurement_process sdmp
        WHERE sdmp.study=%s ;
        ''', (study_name,))
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

    def _get_study_names(self, study: str | None = None) -> list[str]:
        if study is None:
            self.cursor.execute('SELECT name FROM specimen_measurement_study ;')
            rows = self.cursor.fetchall()
        else:
            self.cursor.execute('''
            SELECT sms.name FROM specimen_measurement_study sms
            JOIN study_component sc ON sc.component_study=sms.name
            WHERE sc.primary_study=%s
            ;
            ''', (study,))
            rows = self.cursor.fetchall()
        return sorted([row[0] for row in rows])

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
        progress_reporter = FractionalProgressReporter(
            specimen_count,
            parts=6,
            task_and_done_message=(f'parsing shapefiles for {study}', None),
            logger=logger,
        )
        for row in rows:
            if current_specimen != row[field['specimen']]:
                study_data[current_specimen] = specimen_centroids
                progress_reporter.increment(iteration_details=current_specimen)
                current_specimen = row[field['specimen']]
                specimen_centroids = {}
            specimen_centroids[int(row[field['structure']])] = self._compute_centroid(
                extract_points(row[field['base64_contents']])
            )
        progress_reporter.done()
        study_data[current_specimen] = specimen_centroids
        return study_data

    def _compute_centroid(self, points: list[tuple[float, float]]) -> tuple[float, float]:
        nonrepeating_points = points[0:(len(points)-1)]
        return (
            mean([point[0] for point in nonrepeating_points]),
            mean([point[1] for point in nonrepeating_points]),
        )

    def get_structure_centroids(self) -> StructureCentroids:
        return self._structure_centroids
