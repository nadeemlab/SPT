"""Prepare data extracts from DB for parallel graph creation."""

from argparse import ArgumentParser
from os.path import join
from pickle import dump

from tqdm import tqdm  # type: ignore

from spatialprofilingtoolbox.cggnn.extract import extract_cggnn_data
from spatialprofilingtoolbox.cggnn.generate_graphs import prepare_graph_generation_by_specimen
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument


def parse_arguments():
    """Process command line arguments."""
    parser = ArgumentParser(
        prog='spt cggnn prepare-graph-creation',
        description="""Create files necessary for parallelized graph creation.

Intended to be used with parallel calls to create-specimen-graphs, followed by finalize-graphs.
"""
    )
    add_argument(parser, 'database config')
    add_argument(parser, 'study name')
    parser.add_argument(
        '--strata',
        nargs='+',
        type=int,
        help='Specimen strata to use as labels, identified according to the "stratum identifier" '
             'in `explore-classes`. This should be given as space separated integers.\n'
             'If not provided, all strata will be used.',
        required=False,
        default=None
    )
    parser.add_argument(
        '--validation_data_percent',
        type=int,
        help='Percentage of data to use as validation data. Set to 0 if you want to do k-fold '
        'cross-validation later. (Training percentage is implicit.) Default 15%%.',
        default=15,
        required=False
    )
    parser.add_argument(
        '--test_data_percent',
        type=int,
        help='Percentage of data to use as the test set. (Training percentage is implicit.) '
        'Default 15%%.',
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
        '--include_unlabeled',
        action='store_true',
        help='Include specimens without labels.',
    )
    parser.add_argument(
        '--output_directory',
        type=str,
        help='Save files to this directory.',
        default='tmp',
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
    df_cell, df_label, label_to_result = extract_cggnn_data(
        args.database_config_file,
        args.study_name,
        args.strata,
    )
    specimens_directory = join(args.output_directory, 'specimens')
    p_validation, p_test, roi_size, roi_area, features_to_use, grouped = \
        prepare_graph_generation_by_specimen(
            df_cell,
            df_label,
            args.validation_data_percent,
            args.test_data_percent,
            not args.disable_channels,
            not args.disable_phenotypes,
            args.roi_side_length,
            args.cells_per_slide_target,
            specimens_directory,
            args.random_seed,
        )
    target_name = None if (args.target_name.lower() == 'none') else args.target_name
    with open(join(args.output_directory, 'parameters.pkl'), 'wb') as f:
        dump((
            target_name,
            roi_size,
            roi_area,
            features_to_use,
            df_label,
            p_validation,
            p_test,
            args.random_seed,
        ), f)
    for specimen, df_specimen in tqdm(grouped):
        # Skip specimens without labels
        if (not args.include_unlabeled) and (specimen not in df_label.index):
            continue
        df_specimen.to_hdf(join(specimens_directory, f'{specimen}.h5'), 'cells')
