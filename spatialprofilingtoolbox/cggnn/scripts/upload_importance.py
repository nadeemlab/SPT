"""Uploads importance score output from a cg-gnn instance to the local db."""

from argparse import ArgumentParser

from pandas import read_csv

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.db.importance_score_transcriber import transcribe_importance


def parse_arguments():
    """Process command line arguments."""
    parser = ArgumentParser(
        prog='spt cggnn upload-importance',
        description='Upload importance score output from a cg-gnn model to db.'
    )
    parser.add_argument(
        '--filename',
        type=str,
        help='',
        required=True
    )
    parser.add_argument(
        '--cohort_stratifier',
        type=str,
        help='Name of the classification cohort variable the GNN was trained on to produce '
             'importance_score.',
        required=True
    )
    parser.add_argument(
        '--database_config_file',
        type=str,
        help='Path to database config file.',
        required=True
    )
    parser.add_argument(
        '--per_specimen_selection_number',
        type=str,
        help='The number of most important cells from each specimen that will be selected (or '
             'fewer if there aren\'t enough cells in the specimen).',
        required=False,
        default=1000
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    with DatabaseConnectionMaker(args.database_config_file) as dcm:
        transcribe_importance(
            read_csv(args.filename, index_col=0),
            args.cohort_stratifier,
            dcm.get_connection(),
            args.per_specimen_selection_number,
        )
