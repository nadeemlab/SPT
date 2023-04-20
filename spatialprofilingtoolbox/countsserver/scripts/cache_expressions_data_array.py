"""
Pull expression data from SPT database and store as compressed binary cache.
Also pulls location data.
"""
import argparse
from os.path import abspath
from os.path import expanduser
from os import getcwd
import sys

from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('cache-expressions-data-array')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt countsserver cache-expressions-data-array',
        description='Preload data structure to efficiently serve samples satisfying given partial'
                    ' signatures.'
    )
    add_argument(parser, 'database config')
    parser.add_argument('--centroids-only', dest='centroids_only', action='store_true')
    args = parser.parse_args()

    from spatialprofilingtoolbox.standalone_utilities.module_load_error \
        import SuggestExtrasException
    try:
        from spatialprofilingtoolbox.workflow.common.sparse_matrix_puller import SparseMatrixPuller
        from spatialprofilingtoolbox.countsserver.compressed_matrix_writer \
            import CompressedMatrixWriter
        from spatialprofilingtoolbox.workflow.common.structure_centroids_puller \
            import StructureCentroidsPuller
    except ModuleNotFoundError as e:
        SuggestExtrasException(e, 'workflow')

    database_config_file = abspath(expanduser(args.database_config_file))

    with StructureCentroidsPuller(database_config_file) as puller:
        puller.pull()
        puller.get_structure_centroids().write_to_file(getcwd())

    if args.centroids_only:
        sys.exit()

    with SparseMatrixPuller(database_config_file) as puller:
        puller.pull()
        data_arrays = puller.get_data_arrays()

    writer = CompressedMatrixWriter()
    writer.write(data_arrays)
