import os
from os.path import join
FIND_FILES_USING_PATH = ('FIND_FILES_USING_PATH' in os.environ)
import csv

import pandas as pd

from .log_formats import colorized_logger

logger = colorized_logger(__name__)

def extract_compartments(dataset_settings, cell_manifest_descriptor):
    compartments = []
    file_manifest = pd.read_csv(dataset_settings.file_manifest_file, sep='\t', na_filter=False)
    for i, row in file_manifest.iterrows():
        if row['Data type'] == cell_manifest_descriptor:
            if FIND_FILES_USING_PATH:
                filename = join(dataset_settings.input_path, row['File name'])
            else:
                filename = row['File name']
            new_compartments = extract_compartments_single_file(filename)
            compartments = list(set(compartments).union(new_compartments))
    return sorted(compartments)

def extract_compartments_single_file(filename):
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        header_row = next(reader)
        key = {header_row[i] : i for i in range(len(header_row))}
        entry = lambda row, name: row[key[name]]
        if not 'Classifier Label' in header_row:
            logger.error('"Classifier Label" is missing from file "%s".', filename)
        compartments = [
            entry(row, 'Classifier Label')
            for row in reader
        ]
        return sorted(list(set(compartments)))
