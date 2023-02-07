"""CLI arguments solicitation."""
from typing import Literal
from typing import Union
from typing import get_args
from typing import cast
from argparse import ArgumentParser

from spatialprofilingtoolbox import get_workflow_names


SettingArgumentName = Literal['workflow', 'metrics database', 'source file identifier',
                              'source file name', 'sample', 'outcome', 'dichotomize',
                              'database config', 'file manifest', 'study name']
FileArgumentName = Literal['phenotypes file', 'channels file', 'compartments file',
                           'study file', 'outcomes file', 'subjects file', 'diagnosis file',
                           'interventions file', 'performance report']


def add_argument(parser: ArgumentParser, name: Union[SettingArgumentName, FileArgumentName]):
    if name in get_args(FileArgumentName):
        add_file_argument(parser, cast(FileArgumentName, name))

    if name == 'workflow':
        parser.add_argument('--workflow', dest='workflow', choices=get_workflow_names(),
                            required=True)
    if name == 'metrics database':
        parser.add_argument('--metrics-database-filename', dest='metrics_database_filename',
                            type=str, required=False,
                            help='Filename for sqlite database file storing intermediate results.')
    if name == 'source file identifier':
        parser.add_argument('--input-file-identifier', dest='input_file_identifier', type=str,
                            required=True,
                            help='An input file identifier, as it appears in the file manifest.')
    if name == 'source file name':
        parser.add_argument('--input-filename', dest='input_filename', type=str, required=True)
    if name == 'sample':
        parser.add_argument('--sample-identifier', dest='sample_identifier', type=str,
                            required=True,
                            help='The sample identifier associated with the given input file, as '
                            'it appears in the file manifest.')
    if name == 'outcome':
        parser.add_argument('--outcome', dest='outcome', type=str, required=True,
                            help='The outcome assignment for the sample associated with the given '
                            'input file.')
    if name == 'dichotomize':
        parser.add_argument('--dichotomize', dest='dichotomize', action='store_true')
    if name == 'database config':
        parser.add_argument('--database-config-file', dest='database_config_file', type=str,
                            help='Provide the file for database configuration.')
    if name == 'file manifest':
        parser.add_argument('--file-manifest-file', dest='file_manifest_file', type=str,
                            required=False)
    if name == 'study name':
        parser.add_argument('--study-name', dest='study_name', type=str, required=False,
                            help='The name of the study/dataset to do the workflow computation'
                                 ' over.')


def add_file_argument(parser, name: FileArgumentName):
    if name == 'study file':
        parser.add_argument('--study-file', dest='study_file', type=str, required=False)
    if name == 'outcomes file':
        parser.add_argument('--outcomes-file', dest='outcomes_file', type=str, required=False,
                            help='The outcome assignments file.')
    if name == 'subjects file':
        parser.add_argument('--subjects-file', dest='subjects_file', type=str, required=False,
                            help='File containing subject information: age at specimen collection,'
                            ' sex, diagnosis.')
    if name == 'diagnosis file':
        parser.add_argument('--diagnosis-file', dest='diagnosis_file', type=str, required=False)
    if name == 'interventions file':
        parser.add_argument('--interventions-file', dest='interventions_file', type=str,
                            required=False)
    if name == 'compartments file':
        parser.add_argument('--compartments-file', dest='compartments_file', type=str,
                            required=False, help='File containing compartment names.')
    if name == 'phenotypes file':
        parser.add_argument('--composite-phenotypes-file', dest='composite_phenotypes_file',
                            type=str, required=False)
    if name == 'channels file':
        parser.add_argument('--elementary-phenotypes-file', dest='elementary_phenotypes_file',
                            type=str, required=False)
    if name == 'performance report':
        parser.add_argument('--performance-report-filename', dest='performance_report_filename',
                            type=str, required=False)
