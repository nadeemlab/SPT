"""Extract information cg-gnn needs from SPT and save to file."""

from argparse import ArgumentParser
from os import makedirs
from os.path import join
from os.path import exists
from json import dump

from spatialprofilingtoolbox.cggnn.extract import extract_cggnn_data


def parse_arguments():
    """Process command line arguments."""
    parser = ArgumentParser(
        prog='spt cggnn extract',
        description="""Extract information cg-gnn needs from SPT and save to file.

This command is intended to be used after you've identified which strata you want to keep using `spt
cggnn explore-classes`.

```bash
spt cggnn extract --spt_db_config_location <config_file_location> --study <study_name>
    --strata <strata_to_keep> --output_location <output_folder>
```

Given the strata you want to keep as an unadorned list of integers, e.g., `--strata 9 10` (this
parameter can be skipped if you simply want all strata), this extracts single-cell data and
strata/class information to three files in the output location/folder/directory you provide:
    * `cells.h5`, a binary HDF5 file containing cell information at the individual cell level, such
      as its xy position, channel, and phenotype expressions, as a pandas DataFrame.
    * `labels.h5`, a binary HDF file of a pandas DataFrame containing the class label of each tissue
      specimen as an integer ID, which is automatically derived from the strata information.
    * `label_to_result.json` is a simple JSON that translates each label ID to a human-interpretable
      description, for use in visualizations after training.

These files can be used with the standalone `cg-gnn` pip package to create cell graphs, train a
model on them, and generate summary statistics and graphs from the model.
"""
    )
    parser.add_argument(
        '--spt_db_config_location',
        type=str,
        help='Location of the SPT DB config file.',
        required=True
    )
    parser.add_argument(
        '--study',
        type=str,
        help='Name of the study to query data for.',
        required=True
    )
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
        '--output_location',
        type=str,
        help='Directory to save extracted data to.',
        required=True
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    output_location: str = join(args.output_location, args.study)
    assert isinstance(output_location, str)
    makedirs(output_location, exist_ok=True)
    dict_filename = join(output_location, 'label_to_result.json')
    cells_filename = join(output_location, 'cells.h5')
    labels_filename = join(output_location, 'labels.h5')
    if not (exists(dict_filename) and exists(cells_filename) and exists(labels_filename)):
        df_cell, df_label, label_to_result = extract_cggnn_data(
            args.spt_db_config_location,
            args.study,
            args.strata,
        )
        df_cell.to_hdf(cells_filename, 'cells')
        df_label.to_hdf(labels_filename, 'labels')
        with open(dict_filename, 'w', encoding='utf-8') as f:
            dump(label_to_result, f)
