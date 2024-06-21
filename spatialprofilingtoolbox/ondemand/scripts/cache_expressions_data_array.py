"""Pull expression data from SPT database and store as compressed binary cache. Also pulls location
data.
"""
from typing import cast
import argparse
from os.path import abspath
from os.path import expanduser

from spatialprofilingtoolbox.db.study_tokens import StudyCollectionNaming
from spatialprofilingtoolbox.ondemand.fast_cache_assessor import FastCacheAssessor
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt ondemand cache-expressions-data-array')

def main():
    parser = argparse.ArgumentParser(
        prog='spt ondemand cache-expressions-data-array',
        description='Preload data structure to efficiently serve samples satisfying given partial'
                    ' signatures.'
    )
    add_argument(parser, 'database config')
    parser.add_argument('--centroids-only', dest='centroids_only', action='store_true')
    parser.add_argument('--study-file', dest='study_file', required=False,
        help='''
        If provided, the contents of this file should be the name of a study to which to restrict
        the caching operation.
        '''
    )
    args = parser.parse_args()

    database_config_file = cast(str, args.database_config_file)
    if database_config_file in ['none', 'None']:
        database_config_file = None
    if database_config_file is not None:
        database_config_file = abspath(expanduser(database_config_file))

    study = None
    if args.study_file is not None:
        study = StudyCollectionNaming.extract_study_from_file(args.study_file)

    assessor = FastCacheAssessor(database_config_file, study=study)
    assessor.assess_and_act()

if __name__ == '__main__':
    main()
