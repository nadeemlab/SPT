import argparse

import spatialprofilingtoolbox
from spatialprofilingtoolbox.module_load_error import SuggestExtrasException
try:
    from spatialprofilingtoolbox.workflow.environment.extract_compartments import extract_compartments
    from spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign
    compartment_column_name = HALOCellMetadataDesign.get_compartment_column_name()
except ModuleNotFoundError as e:
    SuggestExtrasException(e, 'workflow')


if __name__=='__main__':
    parser = argparse.ArgumentParser(
        description = 'Scan HALO cell manifest files for compartment names.',
    )
    parser.add_argument(
        'cell_manifest',
        nargs='+',
        type=str,
    )
    parser.add_argument(
        '--compartments-list-file',
        dest='compartments_list_file',
        type=str,
        required=True,
        help='Filename for output list of compartment names.',
    )
    args = parser.parse_args()

    cell_manifests = args.cell_manifest
    compartments_list_file = args.compartments_list_file

    compartments = extract_compartments(cell_manifests)
    with open(compartments_list_file, 'wt') as file:
        file.write('\n'.join(compartments))