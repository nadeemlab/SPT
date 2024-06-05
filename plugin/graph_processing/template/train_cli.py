#!/usr/bin/env python3
"""Process arguments to training command."""

from argparse import ArgumentParser

DEFAULT_CONFIG_FILE = 'training.config'


def parse_arguments():
    """Parse arguments."""
    arg_parser = ArgumentParser()
    arg_parser.add_argument(
        '--input_directory',
        type=str,
        help='Path to the directory containing the cell graphs to be used for training.',
    )
    arg_parser.add_argument(
        '--config_file',
        type=str,
        help='Path to config file.',
        default=DEFAULT_CONFIG_FILE,
    )
    arg_parser.add_argument(
        '--output_directory',
        type=str,
        help='Path to the directory containing the cell graphs to be used for training.',
    )
    return arg_parser.parse_args()
