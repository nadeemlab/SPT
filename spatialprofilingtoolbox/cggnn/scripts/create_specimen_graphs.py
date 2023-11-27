"""Creates graphs from a single specimen."""

from typing import cast
from argparse import ArgumentParser
from os import makedirs
from os.path import join, basename, splitext
from pickle import load

from pandas import read_hdf
from pandas import DataFrame
from dgl import save_graphs  # type: ignore

from spatialprofilingtoolbox.cggnn.generate_graphs import create_graphs_from_specimen


def parse_arguments():
    """Process command line arguments."""
    parser = ArgumentParser(
        prog='spt cggnn create-specimen-graphs',
        description="""Generate graphs from a single specimen.

Intended to be used with prepare-graph-creation and finalize-graphs.
"""
    )
    parser.add_argument(
        '--specimen_hdf_path',
        type=str,
        help='Path to the specimen cell attributes HDF.',
        required=True
    )
    parser.add_argument(
        '--parameters_path',
        type=str,
        help='Path to the graph creation parameter pickle file.',
        required=True
    )
    parser.add_argument(
        '--output_directory',
        type=str,
        help='Save files to this directory.',
        default='tmp/graphs',
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
    with open(args.parameters_path, 'rb') as f:
        (target_name, roi_size, roi_area, features_to_use, _, _, _, random_seed) = load(f)
    graphs = create_graphs_from_specimen(
        cast(DataFrame, read_hdf(args.specimen_hdf_path)),
        features_to_use,
        roi_size,
        roi_area,
        target_name=target_name,
        random_seed=random_seed,
    )
    makedirs(args.output_directory, exist_ok=True)
    save_graphs(join(
        args.output_directory,
        f'{splitext(basename(args.specimen_hdf_path))[0]}.bin',
    ), graphs)
