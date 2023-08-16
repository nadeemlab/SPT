"""Pull expression data from SPT database and store as compressed binary cache. Also pulls location
data.
"""
import argparse
from os.path import abspath
from os.path import expanduser
from os import getcwd
import sys

from spatialprofilingtoolbox import DatabaseConnectionMaker
from spatialprofilingtoolbox.db.expressions_table_indexer import ExpressionsTableIndexer
from spatialprofilingtoolbox.workflow.common.structure_centroids import StructureCentroids
from spatialprofilingtoolbox.workflow.common.structure_centroids import CENTROIDS_FILENAME
from spatialprofilingtoolbox.ondemand.defaults import EXPRESSIONS_INDEX_FILENAME
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('cache-expressions-data-array')

def main():
    parser = argparse.ArgumentParser(
        prog='spt ondemand cache-expressions-data-array',
        description='Preload data structure to efficiently serve samples satisfying given partial'
                    ' signatures.'
    )
    add_argument(parser, 'database config')
    parser.add_argument('--centroids-only', dest='centroids_only', action='store_true')
    args = parser.parse_args()

    database_config_file = args.database_config_file
    if database_config_file == 'none':
        database_config_file = None
    if database_config_file is not None:
        database_config_file = abspath(expanduser(database_config_file))

    if not StructureCentroids.already_exists(getcwd()):
        with DatabaseConnectionMaker(database_config_file) as dcm:
            with dcm.get_connection().cursor() as cursor:
                puller = StructureCentroidsPuller(cursor)
                puller.pull()
                puller.get_structure_centroids().write_to_file(getcwd())
    else:
        logger.info('%s already exists, skipping shapefile pull.', CENTROIDS_FILENAME)

    if args.centroids_only:
        sys.exit()

    if CompressedMatrixWriter.already_exists(getcwd()):
        logger.info('%s already exists, skipping feature matrix pull.', EXPRESSIONS_INDEX_FILENAME)
        sys.exit(1)
    else:
        message = '%s was not found, will do feature matrix pull after all.'
        logger.info(message, EXPRESSIONS_INDEX_FILENAME)

    with DatabaseConnectionMaker(database_config_file) as dcm:
        connection = dcm.get_connection()
        ExpressionsTableIndexer.ensure_indexed_expressions_table(connection)
        with connection.cursor() as cursor:
            puller = SparseMatrixPuller(cursor)
            puller.pull()
            data_arrays = puller.get_data_arrays()

    writer = CompressedMatrixWriter()
    writer.write(data_arrays)

if __name__ == '__main__':
    from spatialprofilingtoolbox.standalone_utilities.module_load_error \
        import SuggestExtrasException
    try:
        from spatialprofilingtoolbox.workflow.common.sparse_matrix_puller import SparseMatrixPuller
        from spatialprofilingtoolbox.ondemand.compressed_matrix_writer \
            import CompressedMatrixWriter
        from spatialprofilingtoolbox.workflow.common.structure_centroids_puller \
            import StructureCentroidsPuller
    except ModuleNotFoundError as e:
        SuggestExtrasException(e, 'workflow')

    main()
