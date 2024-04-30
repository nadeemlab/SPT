"""Utility to promote a dataset from a (private) collection to the general, public collection."""

import argparse

from spatialprofilingtoolbox.db.database_connection import get_and_validate_database_config
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.db.publish_promote import PublisherPromoter


def parse_args():
    parser = argparse.ArgumentParser(
        prog='spt db publish',
        description='Promote a dataset from a (private) collection to the general, public '
                    'collection.'
    )
    add_argument(parser, 'database config')
    parser.add_argument(
        '--study-name',
        dest='study_name',
        help='The fully-qualified name of the study to promote to public status (i.e. including '
             '"collection: ...").',
        required=True
    )
    return parser.parse_args()


def main():
    args = parse_args()
    database_config_file = get_and_validate_database_config(args)
    study = args.study_name
    promoter = PublisherPromoter(database_config_file)
    promoter.promote(study)


if __name__=='__main__':
    main()
