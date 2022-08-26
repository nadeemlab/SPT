import argparse

import spatialprofilingtoolbox
from spatialprofilingtoolbox.module_load_error import SuggestExtrasException
from spatialprofilingtoolbox import workflow_names
from spatialprofilingtoolbox import get_workflow
from spatialprofilingtoolbox import get_integrator
try:
    from spatialprofilingtoolbox.workflow.workflows.defaults.computational_design import ComputationalDesign
    from spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign
except ModuleNotFoundError as e:
    SuggestExtrasException(e, 'workflow')

if __name__=='__main__':
    parser = argparse.ArgumentParser(
        description='''
        Create a list of core, parallelizable job specifications for a given SPT
        workflow, as well as lists of file dependencies.
        
        Note: Due to orchestration design constraints, if this script must
        depend on file contents, it can *only* depend on the contents of explicitly
        indicated files. That is, it cannot "bootstrap" and open files whose names
        are discovered by reading other files' contents.
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

    workflows = {name : get_workflow(name) for name in workflow_names}
    computational_designs = [
        w.computational_design
        for w in workflows.values()
    ]
    for module in computational_designs + [HALOCellMetadataDesign, ComputationalDesign]:
        module.solicit_cli_arguments(parser)

    args = vars(parser.parse_args())
    integrator = get_integrator(**args)
    integrator.calculate(args['stats_tests_file'])
