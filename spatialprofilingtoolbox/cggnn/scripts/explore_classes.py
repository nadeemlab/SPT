"""Report the different strata available to classify with."""

from argparse import ArgumentParser

from spatialprofilingtoolbox.db.feature_matrix_extractor import FeatureMatrixExtractor


def parse_arguments():
    """Process command line arguments."""
    parser = ArgumentParser(
        prog='spt cggnn explore_classes',
        description='See the strata available to classify on.'
    )
    parser.add_argument(
        '--spt_db_config_location',
        type=str,
        help='Location of the SPT DB config file.',
        required=True
    )
    parser.add_argument(
        '--study',
        type=str,
        help='Name of the study to query data for.',
        required=True
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    extractor = FeatureMatrixExtractor(database_config_file=args.spt_db_config_location)
    strata = extractor.extract_cohorts(study=args.study)['strata']
    print(strata.to_string())
