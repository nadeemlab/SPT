"""Train a CG-GNN on pre-split sets of cell graphs."""

import sys
from os import getcwd, system
from argparse import ArgumentParser


def parse_arguments():
    """Parse command line arguments."""
    parser = ArgumentParser(
        prog='spt cggnn train',
        description='Train a GNN on cell graphs.',
    )
    parser.add_argument(
        '--cg_directory',
        type=str,
        help='Directory with the cell graphs, metadata, and feature names. '
        'Model results and any other output will be saved to this directory.',
        required=True
    )
    parser.add_argument(
        '--in_ram',
        help='If the data should be stored in RAM.',
        action='store_true',
    )
    parser.add_argument(
        '-b',
        '--batch_size',
        type=int,
        help='Batch size to use during training.',
        default=1,
        required=False
    )
    parser.add_argument(
        '--epochs',
        type=int,
        help='Number of training epochs to do.',
        default=10,
        required=False
    )
    parser.add_argument(
        '-l',
        '--learning_rate',
        type=float,
        help='Learning rate to use during training.',
        default=1e-3,
        required=False
    )
    parser.add_argument(
        '-k',
        '--k_folds',
        type=int,
        help='Folds to use in k-fold cross validation. 0 means don\'t use k-fold cross validation '
        'unless no validation dataset is provided, in which case k defaults to 3.',
        required=False,
        default=0
    )
    parser.add_argument(
        '--explainer',
        type=str,
        help='Which explainer type to use. If provided, importance scores will be calculated.',
        default=None,
        required=False
    )
    parser.add_argument(
        '--merge_rois',
        help='Save a CSV of importance scores merged across ROIs from a single specimen.',
        action='store_true'
    )
    parser.add_argument(
        '--random_seed',
        type=int,
        help='Random seed to use for reproducibility.',
        default=None,
        required=False
    )
    parser.add_argument(
        '--cuda',
        help='Train a CUDA-enabled CG-GNN. Defaults to CPU if not provided.',
        action='store_true'
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    args_to_pass = [f'"{arg}"' for arg in sys.argv[1:]]
    if args.cuda:
        container = '-cuda'
        args_to_pass.remove('--cuda')
    else:
        container = ''
    system(
        f'docker run --rm -v "{getcwd()}:/app" nadeemlab/spt-cg-gnn:latest{container} '
        ' '.join(args_to_pass)
    )
