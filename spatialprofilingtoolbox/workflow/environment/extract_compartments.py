import csv

from ...standalone_utilities.log_formats import colorized_logger
from ..dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign

compartment_column_name = HALOCellMetadataDesign.get_compartment_column_name()
logger = colorized_logger(__name__)


def extract_compartments_single_file(filename):
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        header_row = next(reader)
        key = {header_row[i] : i for i in range(len(header_row))}
        entry = lambda row, name: row[key[name]]
        if not compartment_column_name in header_row:
            logger.warning('"%s" is missing from file "%s".', compartment_column_name, filename)
            compartments = [
                '<any>'
                for row in reader
            ]
        else:
            compartments = [
                entry(row, compartment_column_name)
                for row in reader
            ]
        return sorted(list(set(compartments)))


def extract_compartments(cell_manifests):
    compartments = set([])
    for cell_manifest in cell_manifests:
        compartments = compartments.union(set(
            extract_compartments_single_file(cell_manifest)
        ))
    compartments = sorted(list(compartments))
    return compartments
