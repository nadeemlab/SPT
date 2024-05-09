"""GNN importance fractions figure generation

This is generated programmatically from extractions from Graph Neural Network models.
"""

from argparse import ArgumentParser

import matplotlib.pyplot as plt

from spatialprofilingtoolbox.graphs.config_reader import read_plot_importance_fractions_config
from spatialprofilingtoolbox.graphs.graph_plugin_plots import PlotGenerator


def parse_arguments():
    """Process command line arguments."""
    parser = ArgumentParser(
        prog='spt graphs plot-importance-fractions',
        description="""Generate GNN-derived importance score fractions plot."""
    )
    parser.add_argument(
        '--config_path',
        type=str,
        help='Path to the configuration TOML file.',
        required=True,
    )
    parser.add_argument(
        '--output_filename',
        type=str,
        default=None,
        help='Filename (including extension) to save the plot to.',
    )
    parser.add_argument(
        '--show',
        action='store_true',
        help='If set, will display figures in addition to saving.',
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    if not args.show and (args.output_filename is None):
        raise ValueError('Nothing requested of the plot, skipping.')
    (
        db_config_file_path,
        study_name,
        phenotypes,
        plugins,
        figure_size,
        orientation,
    ) = read_plot_importance_fractions_config(args.config_path)
    generator = PlotGenerator(
        db_config_file_path,
        study_name,
        phenotypes,
        plugins,
        figure_size,
        orientation,
    )
    fig = generator.generate_plot()
    if args.output_filename is not None:
        plt.savefig(args.output_filename)
    if args.show:
        plt.show()
