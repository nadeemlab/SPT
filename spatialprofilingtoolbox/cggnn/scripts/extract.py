"""Extract information cg-gnn needs from SPT and save to file."""

from argparse import ArgumentParser
from os.path import join, exists
from json import dump

from spatialprofilingtoolbox.cggnn import extract_cggnn_data


def parse_arguments():
    """Process command line arguments."""
    parser = ArgumentParser(
        prog='spt cggnn extract',
        description='Extract information cg-gnn needs from SPT and save to file.'
    )
    parser.add_argument(
        '--spt_db_config_location',
        type=str,
        help='File location for SPT DB config file.',
        required=True
    )
    parser.add_argument(
        '--study',
        type=str,
        help='Name of the study to query data for in SPT.',
        required=True
    )
    parser.add_argument(
        '--output_location',
        type=str,
        help='Directory to save extracted data to.',
        required=True
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    df_cell, df_label, label_to_result = extract_cggnn_data(args.spt_db_config_location, args.study)

    assert isinstance(args.output_location, str)
    dict_filename = join(args.output_location, 'label_to_results.json')
    cells_filename = join(args.output_location, 'cells.h5')
    labels_filename = join(args.output_location, 'labels.h5')
    if not (exists(dict_filename) and exists(cells_filename) and exists(labels_filename)):
        df_cell.to_hdf(cells_filename, 'cells')
        df_label.to_hdf(labels_filename, 'labels')
        dump(label_to_result, open(dict_filename, 'w', encoding='utf-8'))
