"""Do cache file pulling/creation and stashing in database."""

import brotli

from spatialprofilingtoolbox.db.accessors.cells import CellsAccess
from spatialprofilingtoolbox.db.database_connection import DBCursor, retrieve_study_names
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
from spatialprofilingtoolbox.workflow.common.sparse_matrix_puller import SparseMatrixPuller
from spatialprofilingtoolbox.workflow.common.structure_centroids_puller \
    import StructureCentroidsPuller
from spatialprofilingtoolbox.workflow.common.umap_creation import UMAPCreator

logger = colorized_logger(__name__)

def cache_pull(database_config_file: str | None, centroids_only: bool = False, study: str | None = None):
    puller1 = StructureCentroidsPuller(database_config_file)
    puller1.pull_and_write_to_files(study=study)
    if centroids_only:
        return
    puller2 = SparseMatrixPuller(database_config_file)
    puller2.pull_and_write_to_files(study=study)

    if study is None:
        study_names = tuple(retrieve_study_names(database_config_file))
    else:
        study_names = (study,)

    for study_name in study_names:
        measurement_study = puller2._get_measurement_study_name(study_name)
        specimens = puller2._get_pertinent_specimens(study_name=study_name, measurement_study=measurement_study)

        with DBCursor(database_config_file=database_config_file, study=study_name) as cursor:
            access = CellsAccess(cursor)

            for specimen in specimens:
                raw = access._zip_location_and_phenotype_data(
                    access._get_location_data(specimen, cell_identifiers=()),
                    access._get_phenotype_data(specimen, cell_identifiers=()),
                )

                compressed_data = brotli.compress(raw, quality=11, lgwin=24)

                cursor.execute('''
                    INSERT INTO
                    ondemand_studies_index (
                        specimen,
                        blob_type,
                        blob_contents
                    )
                    VALUES (%s, %s, %s);
                ''', (specimen, 'cell_data_brotli', compressed_data))

                logger.info('Created brotli compressed cell_data for %s', specimen)

def umap_cache_pull(database_config_file: str | None, study: str | None = None):
    if study is None:
        studies = tuple(retrieve_study_names(database_config_file))
    else:
        studies = (study,)
    for _study in studies:
        creator = UMAPCreator(database_config_file, _study)
        creator.create()
