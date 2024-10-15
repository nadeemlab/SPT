"""
Pull expression data from SPT database and store as compressed binary cache. Also pulls location
data.
"""
from typing import cast
import argparse
from os.path import abspath
from os.path import expanduser
import os

from spatialprofilingtoolbox.db.credentials import retrieve_credentials_from_file
from spatialprofilingtoolbox.db.study_tokens import StudyCollectionNaming
from spatialprofilingtoolbox.ondemand.cache_assessment import CacheAssessment
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt ondemand assess-recreate-cache')

def main():
    parser = argparse.ArgumentParser(
        prog='spt ondemand assess-recreate-cache',
        description='Preload data structure to efficiently serve sample data.'
    )
    add_argument(parser, 'database config')
    parser.add_argument('--study-file', dest='study_file', required=True,
        help='''
        This file should be a JSON file with "Study name" key that is the name of a
        study to which to restrict the caching operation.
        '''
    )
    args = parser.parse_args()

    database_config_file = cast(str, args.database_config_file)
    if database_config_file in ['none', 'None']:
        database_config_file = None
    if database_config_file is not None:
        database_config_file = abspath(expanduser(database_config_file))

    study = StudyCollectionNaming.extract_study_from_file(args.study_file)

    creds = retrieve_credentials_from_file(database_config_file)

    key = 'SINGLE_CELL_DATABASE_HOST'
    if not key in os.environ:
        os.environ[key] = creds.endpoint
    key = 'SINGLE_CELL_DATABASE_USER'
    if not key in os.environ:
        os.environ[key] = creds.user
    key = 'SINGLE_CELL_DATABASE_PASSWORD'
    if not key in os.environ:
        os.environ[key] = creds.password

    assessor = CacheAssessment(database_config_file, study=study)
    assessor.assess_and_act()

if __name__ == '__main__':
    main()
