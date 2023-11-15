"""Generates graph from saved SPT files."""

from argparse import ArgumentParser

from pandas import read_hdf  # type: ignore

from spatialprofilingtoolbox.cggnn.generate_graphs import generate_graphs


def parse_arguments():
    """Process command line arguments."""
    parser = ArgumentParser(
        prog='spt cggnn generate-graphs',
        description="Generate graphs from saved SPT files."
    )
    parser.add_argument(
        '--spt_hdf_cell_path',
        type=str,
        help='Path to the SPT cell attributes HDF.',
        required=True
    )
    parser.add_argument(
        '--spt_hdf_label_path',
        type=str,
        help='Path to the SPT labels HDF.',
        required=True
    )
    parser.add_argument(
        '--validation_data_percent',
        type=int,
        help='Percentage of data to use as validation data. Set to 0 if you want to do k-fold '
        'cross-validation later. (Training percentage is implicit.) Default 15%.',
        default=15,
        required=False
    )
    parser.add_argument(
        '--test_data_percent',
        type=int,
        help='Percentage of data to use as the test set. (Training percentage is implicit.) '
        'Default 15%.',
        default=15,
        required=False
    )
    parser.add_argument(
        '--disable_channels',
        action='store_true',
        help='Disable the use of channel information in the graph.',
    )
    parser.add_argument(
        '--disable_phenotypes',
        action='store_true',
        help='Disable the use of phenotype information in the graph.',
    )
    parser.add_argument(
        '--roi_side_length',
        type=int,
        help='Side length in pixels of the ROI areas we wish to generate.',
        default=None,
        required=False
    )
    parser.add_argument(
        '--cells_per_slide_target',
        type=int,
        help='Used with the median cell density across all slides to determine the ROI size.',
        default=5_000,
        required=False
    )
    parser.add_argument(
        '--target_name',
        type=str,
        help='If given, build ROIs based only on cells with true values in this DataFrame column.',
        default=None,
        required=False
    )
    parser.add_argument(
        '--output_directory',
        type=str,
        help='Directory to save the (sub)directory of graph files to.',
        default=None,
        required=False
    )
    parser.add_argument(
        '--random_seed',
        type=int,
        help='Random seed to use for reproducibility.',
        default=None,
        required=False
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    generate_graphs(
        read_hdf(args.spt_hdf_cell_path),  # type: ignore
        read_hdf(args.spt_hdf_label_path),  # type: ignore
        args.validation_data_percent,
        args.test_data_percent,
        use_channels=not args.disable_channels,
        use_phenotypes=not args.disable_phenotypes,
        roi_side_length=args.roi_side_length,
        cells_per_slide_target=args.cells_per_slide_target,
        target_name=args.target_name,
        output_directory=args.output_directory,
        random_seed=args.random_seed,
    )
