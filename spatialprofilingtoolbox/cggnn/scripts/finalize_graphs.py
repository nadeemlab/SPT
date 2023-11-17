"""Finalize graphs created via parallel processing."""

from argparse import ArgumentParser
from os.path import basename, splitext
from pickle import load

from dgl import DGLGraph, load_graphs  # type: ignore

from spatialprofilingtoolbox.cggnn.generate_graphs import finalize_graph_metadata


def parse_arguments():
    """Process command line arguments."""
    parser = ArgumentParser(
        prog='spt cggnn finalize-graphs',
        description="""Finalize created graphs.

Splits graphs into train/validation/test sets. This command is intended to be used with
prepare-graph-creation and parallel create-specimen-graphs calls.
"""
    )
    parser.add_argument(
        '--graph_files',
        type=str,
        nargs='+',
        help='Paths to the graph files.',
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
    with open(args.parameters_path, 'rb') as f:
        (_, roi_size, _, features_to_use, df_label, p_validation, p_test, random_seed) = load(f)
    graphs_by_specimen: dict[str, list[DGLGraph]] = {}
    for specimen_graphs_path in args.graph_files:
        graphs_by_specimen[
            splitext(basename(specimen_graphs_path))[0]
        ] = load_graphs(specimen_graphs_path)[0]
    finalize_graph_metadata(
        graphs_by_specimen,
        df_label,
        p_validation,
        p_test,
        roi_size,
        features_to_use=features_to_use,
        output_directory=args.output_directory,
    )
