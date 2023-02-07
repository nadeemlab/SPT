"""
CLI entry point into the wrap-up/integration phase of the Nextflow-managed
workflows.
"""
import argparse

from spatialprofilingtoolbox.workflow.defaults.cli_arguments import add_argument
from spatialprofilingtoolbox import get_workflow_names
from spatialprofilingtoolbox import get_workflow
from spatialprofilingtoolbox import get_integrator

workflows = {name: get_workflow(name) for name in get_workflow_names()}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt workflow aggregate-core-results',
        description='''
        Merge the results provided by all core jobs.
        ''',
    )
    add_argument(parser, 'workflow')
    parser.add_argument(
        '--stats-tests-file',
        dest='stats_tests_file',
        type=str,
        required=False,
    )
    add_argument(parser, 'database config')
    add_argument(parser, 'file manifest')
    add_argument(parser, 'study name')

    from spatialprofilingtoolbox.standalone_utilities.module_load_error import \
        SuggestExtrasException
    try:
        from spatialprofilingtoolbox.workflow.defaults.computational_design import \
            ComputationalDesign
        from \
            spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.\
                halo_cell_metadata_design import HALOCellMetadataDesign
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
    if 'stats_tests_file' in args:
        integrator.calculate(args['stats_tests_file'])
    else:
        integrator.calculate()
