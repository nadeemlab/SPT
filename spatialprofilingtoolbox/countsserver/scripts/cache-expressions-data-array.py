import argparse
from os.path import abspath
from os.path import expanduser

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('cache-expressions-data-array')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt countsserver cache-expressions-data-array',
        description='Server providing counts of samples satisfying given partial signatures.'
    )
    parser.add_argument(
        '--database-config-file',
        dest='database_config_file',
        type=str,
        help='Provide the file for database configuration.',
    )
    args = parser.parse_args()

    from spatialprofilingtoolbox.standalone_utilities.module_load_error \
        import SuggestExtrasException
    try:
        from spatialprofilingtoolbox.workflow.common.sparse_matrix_puller import SparseMatrixPuller
        from spatialprofilingtoolbox.countsserver.compressed_matrix_writer \
            import CompressedMatrixWriter
        from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
    except ModuleNotFoundError as e:
        SuggestExtrasException(e, 'workflow')

    database_config_file = abspath(expanduser(args.database_config_file))

    with SparseMatrixPuller(database_config_file) as puller:
        puller.pull()
        data_arrays = puller.get_data_arrays()

    writer = CompressedMatrixWriter()
    writer.write(data_arrays)
