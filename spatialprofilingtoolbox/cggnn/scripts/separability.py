"""Explain a cell graph (CG) prediction using a pretrained CG-GNN and a graph explainer."""

from argparse import ArgumentParser

from spatialprofilingtoolbox.cggnn.util import load_cell_graphs, load_label_to_result

from spatialprofilingtoolbox.cggnn.histocartography import calculate_separability
from spatialprofilingtoolbox.cggnn.histocartography.util import instantiate_model


def parse_arguments():
    """Process command line arguments."""
    parser = ArgumentParser(
        prog='spt cggnn seperability',
        description='Explain a cell graph prediction using a model and a graph explainer.',
    )
    parser.add_argument(
        '--cg_path',
        type=str,
        help='Directory with the cell graphs, metadata, and feature names.',
        required=True
    )
    parser.add_argument(
        '--feature_names_path',
        type=str,
        help='Path to the list of feature names.',
        required=True
    )
    parser.add_argument(
        '--model_checkpoint_path',
        type=str,
        help='Path to the model checkpoint.',
        required=True
    )
    parser.add_argument(
        '--label_to_result_path',
        type=str,
        help='Where to find the data mapping label ints to their string results.',
        required=False
    )
    parser.add_argument(
        '--prune_misclassified',
        help='Remove entries for misclassified cell graphs when calculating separability scores.',
        action='store_true'
    )
    parser.add_argument(
        '--output_directory',
        type=str,
        help='Where to save the output reporting.',
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


def main():
    args = parse_arguments()
    graphs_data, feature_names = load_cell_graphs(args.cg_path)
    df_concept, df_aggregated, dfs_k_dist = calculate_separability(
        graphs_data,
        instantiate_model(graphs_data, model_checkpoint_path=args.model_checkpoint_path),
        feature_names,
        label_to_result=load_label_to_result(args.label_to_result_path),
        prune_misclassified=args.prune_misclassified,
        out_directory=args.output_directory,
        random_seed=args.random_seed,
    )
    print(df_concept)
    print(df_aggregated)
    for cg_pair, df_k in dfs_k_dist.items():
        print(cg_pair)
        print(df_k)


if __name__ == "__main__":
    main()
