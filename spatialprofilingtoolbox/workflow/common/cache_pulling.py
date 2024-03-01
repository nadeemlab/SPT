"""Do cache file pulling/creation and stashing in database."""

from spatialprofilingtoolbox.workflow.common.sparse_matrix_puller import SparseMatrixPuller
from spatialprofilingtoolbox.workflow.common.structure_centroids_puller \
    import StructureCentroidsPuller

def cache_pull(database_config_file: str | None, centroids_only: bool = False, study: str | None = None):
    puller1 = StructureCentroidsPuller(database_config_file)
    puller1.pull_and_write_to_files(study=study)
    if centroids_only:
        return
    puller2 = SparseMatrixPuller(database_config_file)
    puller2.pull_and_write_to_files(study=study)
