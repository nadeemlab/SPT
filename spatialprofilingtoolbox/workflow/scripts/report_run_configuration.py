"""
CLI entry point into the utility that reports (for informational purposess or
debugging) the configuration of a Nextflow-managed workflow before it runs.
"""
import argparse

from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt workflow report-run-configuration',
        description='''
        Log information about an SPT run configuration.
        '''
    )
    add_argument(parser, 'workflow')
    add_argument(parser, 'file manifest')
    add_argument(parser, 'samples file')
    add_argument(parser, 'channels file')
    add_argument(parser, 'phenotypes file')
    args = parser.parse_args()

    from spatialprofilingtoolbox.standalone_utilities.module_load_error import \
        SuggestExtrasException
    try:
        from spatialprofilingtoolbox.workflow.common.logging.run_configuration_reporter import \
            RunConfigurationReporter
    except ModuleNotFoundError as e:
        SuggestExtrasException(e, 'workflow')

    r = RunConfigurationReporter(**vars(args))
