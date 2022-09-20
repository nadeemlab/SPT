import argparse

if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog = 'spt workflow report-run-configuration',
        description = '''
        Log information about an SPT run configuration.
        '''
    )
    parser.add_argument(
        '--workflow',
        dest='workflow',
        type=str,
    )
    parser.add_argument(
        '--file-manifest-file',
        dest='file_manifest_file',
        type=str,
    )
    parser.add_argument(
        '--outcomes-file',
        dest='outcomes_file',
        type=str,
    )
    parser.add_argument(
        '--elementary-phenotypes-file',
        dest='elementary_phenotypes_file',
        type=str,
    )
    parser.add_argument(
        '--composite-phenotypes-file',
        dest='composite_phenotypes_file',
        type=str,
    )
    parser.add_argument(
        '--compartments-file',
        dest='compartments_file',
        type=str,
    )
    args = parser.parse_args()

    import spatialprofilingtoolbox
    from spatialprofilingtoolbox.standalone_utilities.module_load_error import SuggestExtrasException
    try:
        from spatialprofilingtoolbox.workflow.common.logging.run_configuration_reporter import RunConfigurationReporter
    except ModuleNotFoundError as e:
        SuggestExtrasException(e, 'workflow')

    r = RunConfigurationReporter(**vars(args))
