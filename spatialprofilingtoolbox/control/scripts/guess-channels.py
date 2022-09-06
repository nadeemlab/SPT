import argparse
import csv
import re

def do_library_imports():
    import spatialprofilingtoolbox
    from spatialprofilingtoolbox.module_load_error import SuggestExtrasException
    try:
        import pandas as pd
    except ModuleNotFoundError as e:
        SuggestExtrasException(e, 'control')


def parse_channels(columns):
    patterns = {
        'membership': '^(\w[\w _\d]+)[ _]Positive([ _]Classification)?$',
        'intensity': '^(\w[\w _\d]+)(?<![ _]Nucleus)(?<![ _]Cytoplasm)(?<![ _]Membrane)[ _](Cell[ _])?Intensity$',
    }
    available = {kind : [] for kind in patterns}
    for column in columns:
        for kind, pattern in patterns.items():
            match = re.match(pattern, column)
            if match:
                available[kind].append((match.group(1), column))
    return available

def intersect_available(parsed_columns_list):
    available = parsed_columns_list[0]
    for parsed in parsed_columns_list:
        for kind in ['membership', 'intensity']:
            available[kind] = sorted(list(set(available[kind]).intersection(parsed[kind])))
    return available

def create_elementary_phenotypes_table(available_channels):
    records = []
    for phenotype_string, column in available_channels['membership']:
        records.append({
            'Name' : phenotype_string,
            'Column header fragment prefix' : phenotype_string,
        })
    return pd.DataFrame(records)[['Name', 'Column header fragment prefix']]


if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog = 'spt control guess-channels',
        description = 'Attempt to extract channel information from a list of HALO cell manifest files.',
    )

    parser.add_argument(
        'cell_files',
        nargs='+',
    )
    parser.add_argument(
        '--output-file',
        dest='output_file',
        type=str,
        required=True,
    )

    args = parser.parse_args()

    do_library_imports()

    cell_files = args.cell_files
    known_channels = []
    for cell_file in cell_files:
        with open(cell_file, 'rt') as file:
            reader = csv.reader(file)
            header = next(reader)
        known_channels.append(parse_channels(header))
    available_channels = intersect_available(known_channels)
    elementary_phenotypes = create_elementary_phenotypes_table(available_channels)
    elementary_phenotypes.to_csv(args.output_file, index=False)
