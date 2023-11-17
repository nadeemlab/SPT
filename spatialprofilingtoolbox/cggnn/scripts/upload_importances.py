"""Upload importance score output from a cg-gnn instance to the local db."""

from argparse import ArgumentParser

from pandas import read_csv

from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.db.importance_score_transcriber import transcribe_importance


def parse_arguments():
    """Process command line arguments."""
    parser = ArgumentParser(
        prog='spt cggnn upload-importances',
        description='Save cell importance scores as defined by cggnn to the database.',
    )
    add_argument(parser, 'database config')
    add_argument(parser, 'study name')
    parser.add_argument(
        '--importances_csv_path',
        type=str,
        help='File location for the importances CSV.',
        required=True,
    )
    parser.add_argument(
        '--cohort_stratifier',
        type=str,
        help='Name of the classification cohort variable the GNN was trained on.',
        default='',
        required=False,
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    df = read_csv(args.importances_csv_path, index_col=0)
    transcribe_importance(
        df,
        args.database_config_file,
        args.study_name,
        cohort_stratifier=args.cohort_stratifier,
    )
