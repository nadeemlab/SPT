"""Generate graphs from SPT database extracts."""

from argparse import ArgumentParser

from pandas import read_hdf  # type: ignore

from spatialprofilingtoolbox.graphs.config_reader import read_generation_config
from spatialprofilingtoolbox.graphs.generate_graphs import generate_graphs


def parse_arguments():
    """Process command line arguments."""
    parser = ArgumentParser(
        prog='spt graphs generate-graphs',
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
        '--config_path',
        type=str,
        help='Path to the graph generation configuration TOML file.',
        required=True
    )
    parser.add_argument(
        '--output_directory',
        type=str,
        help='Save files to this directory.',
        default='graphs',
        required=False
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    config_values = read_generation_config(args.config_path)
    generate_graphs(
        read_hdf(args.spt_hdf_cell_path),  # type: ignore
        read_hdf(args.spt_hdf_label_path),  # type: ignore
        *config_values,
        args.output_directory,
    )
