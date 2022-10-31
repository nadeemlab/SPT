import argparse
import os
from os.path import join
from os.path import exists
from os.path import abspath
from os.path import expanduser

import spatialprofilingtoolbox
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
logger = colorized_logger('cache-expressions-data-array')


if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog = 'spt countsserver cache-expressions-data-array',
        description = 'Server providing counts of samples satisfying given partial signatures.'
    )
    parser.add_argument(
        '--database-config-file',
        dest='database_config_file',
        type=str,
        help='Provide the file for database configuration.',
    )
    args = parser.parse_args()

    from spatialprofilingtoolbox.standalone_utilities.module_load_error import SuggestExtrasException
    try:
        from spatialprofilingtoolbox.countsserver.compressed_matrix_puller import CompressedMatrixPuller
    except ModuleNotFoundError as e:
        SuggestExtrasException(e, 'workflow')

    database_config_file = abspath(expanduser(args.database_config_file))
    puller = CompressedMatrixPuller(database_config_file)

