"""Upload importance score output from a cg-gnn instance to the local db."""

from argparse import ArgumentParser

from pandas import read_csv

from spatialprofilingtoolbox.db.importance_score_transcriber import transcribe_importance
from spatialprofilingtoolbox.graphs.config_reader import read_upload_config


def parse_arguments():
    """Process command line arguments."""
    parser = ArgumentParser(
        prog='spt graphs upload-importances',
        description='Save cell importance scores to the database.',
    )
    parser.add_argument(
        '--importances_csv_path',
        type=str,
        help='File location for the importances CSV.',
        required=True
    )
    parser.add_argument(
        '--config_path',
        type=str,
        help='Path to the graph generation configuration TOML file.',
        required=True
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    (
        database_config_file,
        study_name,
        cohort_stratifier,
    ) = read_upload_config(args.config_path)
    df = read_csv(args.importances_csv_path, index_col=0)
    transcribe_importance(
        df,
        database_config_file,
        study_name,
        cohort_stratifier=cohort_stratifier,
    )
