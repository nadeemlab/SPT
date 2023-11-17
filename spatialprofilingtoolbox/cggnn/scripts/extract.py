"""Extract information cg-gnn needs from SPT and save to file."""

from argparse import ArgumentParser
from os import makedirs
from os.path import join
from os.path import exists
from json import dump

from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.cggnn.extract import extract_cggnn_data


def parse_arguments():
    """Process command line arguments."""
    parser = ArgumentParser(
        prog='spt cggnn extract',
        description="""Extract information cg-gnn needs from a single-cell dataset in scstudies database format,
and save to file.

This command is intended to be used after you have identified which strata you want to use with `spt
cggnn explore-classes`.

```bash
spt cggnn extract --database-config-file <config_file_location> --study-name <study_name>
    --strata <strata_to_keep> --output_directory <output_folder>
```

Use an unadorned list of integers, e.g. `--strata 9 10`. This parameter can be skipped to use all
strata.

This extracts single-cell data and strata/class information to three files in the output directory:
    * `cells.h5`, a binary HDF5 file containing cell information at the individual cell level, such
      as its xy position, channel, and phenotype expressions, as a pandas DataFrame.
    * `labels.h5`, a binary HDF file of a pandas DataFrame containing the class label of each tissue
      specimen as an integer ID, which is automatically derived from the strata information.
    * `label_to_result.json` is a simple JSON that translates each label ID to a human-interpretable
      description, for use in visualizations after training.

These files can be used with the standalone `cg-gnn` pip package to create cell graphs, train a
model, and generate summary statistics and graphs from the model.
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
        '--output_directory',
        type=str,
        help='Directory to save extracted data to.',
        required=True
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    output_directory: str = join(args.output_directory, args.study_name)
    assert isinstance(output_directory, str)
    makedirs(output_directory, exist_ok=True)
    dict_filename = join(output_directory, 'label_to_result.json')
    cells_filename = join(output_directory, 'cells.h5')
    labels_filename = join(output_directory, 'labels.h5')
    if not (exists(dict_filename) and exists(cells_filename) and exists(labels_filename)):
        df_cell, df_label, label_to_result = extract_cggnn_data(
            args.database_config_file,
            args.study_name,
            args.strata,
        )
        df_cell.to_hdf(cells_filename, 'cells')
        df_label.to_hdf(labels_filename, 'labels')
        with open(dict_filename, 'w', encoding='utf-8') as f:
            dump(label_to_result, f)
