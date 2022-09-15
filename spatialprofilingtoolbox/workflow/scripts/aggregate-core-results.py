import argparse

import spatialprofilingtoolbox
from spatialprofilingtoolbox import get_workflow_names
from spatialprofilingtoolbox import get_workflow
from spatialprofilingtoolbox import get_integrator
workflows = {name : get_workflow(name) for name in get_workflow_names()}

if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog = 'spt workflow aggregate-core-results',
        description='''
        Merge the results provided by all core jobs.
        ''',
    )
    parser.add_argument(
        '--workflow',
        dest='workflow',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--stats-tests-file',
        dest='stats_tests_file',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--database-config-file',
        dest='database_config_file',
        type=str,
        required=False,
    )
    parser.add_argument(
        '--file-manifest-file',
        dest='file_manifest_file',
        type=str,
        required=False,
    )

    from spatialprofilingtoolbox.standalone_utilities.module_load_error import SuggestExtrasException
    try:
        from spatialprofilingtoolbox.workflow.workflows.defaults.computational_design import ComputationalDesign
        from spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign
    except ModuleNotFoundError as e:
        SuggestExtrasException(e, 'workflow')

    computational_designs = [
        w.computational_design
        for w in workflows.values()
    ]
    for module in computational_designs + [HALOCellMetadataDesign, ComputationalDesign]:
        module.solicit_cli_arguments(parser)

    args = vars(parser.parse_args())

    integrator = get_integrator(**args)
    integrator.calculate(args['stats_tests_file'])
