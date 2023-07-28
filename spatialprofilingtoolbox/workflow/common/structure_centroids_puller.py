"""Retrieves positional information for all cells in the SPT database."""
import statistics

from psycopg2.extensions import cursor as Psycopg2Cursor

from spatialprofilingtoolbox.db.shapefile_polygon import extract_points
from spatialprofilingtoolbox.workflow.common.structure_centroids import StructureCentroids
from spatialprofilingtoolbox.workflow.common.logging.fractional_progress_reporter \
    import FractionalProgressReporter
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class StructureCentroidsPuller:
    """Retrieve positional information for all cells in single cell database."""

    cursor: Psycopg2Cursor
    structure_centroids: StructureCentroids

    def __init__(self, cursor: Psycopg2Cursor):
        self.cursor = cursor
        self.structure_centroids = StructureCentroids()

    def pull(self, specimen: str | None=None, study: str | None=None):
        study_names = self._get_study_names(study=study)
        for study_name in study_names:
            if specimen is None:
                specimen_count = self._get_specimen_count(study_name, self.cursor)
                self.cursor.execute(self._get_shapefiles_query(), (study_name,))
            else:
                specimen_count = 1
                self.cursor.execute(
                    self._get_shapefiles_query_specimen_specific(),
                    (study_name, specimen),
                )
            rows = self.cursor.fetchall()
            if len(rows) == 0:
                continue
            self.structure_centroids.add_study_data(
                study_name,
                self._create_study_data(rows, specimen_count, study_name)
            )

    def _get_specimen_count(self, study_name, cursor):
        cursor.execute('''
        SELECT COUNT(*) FROM specimen_data_measurement_process sdmp
        WHERE sdmp.study=%s ;
        ''', (study_name,))
        return cursor.fetchall()[0][0]

    def _get_shapefiles_query(self):
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

    def _get_shapefiles_query_specimen_specific(self):
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

    def _get_study_names(self, study: str | None=None):
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

    def _create_study_data(self, rows, specimen_count, study):
        study_data = {}
        field = {'structure': 0, 'specimen': 1, 'base64_contents': 2}
        current_specimen = rows[0][field['specimen']]
        specimen_centroids = []
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
                specimen_centroids = []
            specimen_centroids.append(self._compute_centroid(
                extract_points(row[field['base64_contents']])
            ))
        progress_reporter.done()
        study_data[current_specimen] = specimen_centroids
        return study_data

    def _compute_centroid(self, points):
        nonrepeating_points = points[0:(len(points)-1)]
        return (
            statistics.mean([point[0] for point in nonrepeating_points]),
            statistics.mean([point[1] for point in nonrepeating_points]),
        )

    def get_structure_centroids(self) -> StructureCentroids:
        return self.structure_centroids
