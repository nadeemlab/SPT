import csv

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
from \
    spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.halo_cell_metadata_design \
    import HALOCellMetadataDesign

COMPARTMENT_COLUMN_NAME = HALOCellMetadataDesign.get_compartment_column_name()
logger = colorized_logger(__name__)


def extract_compartments_single_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        header_row = next(reader)
        key = {header_row[i]: i for i in range(len(header_row))}

        def entry(row, name):
            return row[key[name]]
        if not COMPARTMENT_COLUMN_NAME in header_row:
            compartments = [
                '<any>'
                for row in reader
            ]
        else:
            compartments = [
                entry(row, COMPARTMENT_COLUMN_NAME)
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
