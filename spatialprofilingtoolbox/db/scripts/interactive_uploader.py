"""CLI utility to drop one feature (values, specification, specifiers) from the database"""
from os import listdir
from os.path import expanduser
from os.path import isfile
from os.path import basename
from os.path import join
from os.path import split
from os.path import abspath
from os.path import isdir
from os import walk as os_walk
from os import environ as os_environ
from os import mkdir
from os import system as os_system
import re
from sys import exit as sys_exit
import argparse
from configparser import ConfigParser
from json import loads as json_loads
from typing import cast

if 'SPT_S3_BUCKET' in os_environ:
    S3_BUCKET = os_environ['SPT_S3_BUCKET']
else:
    S3_BUCKET = None

from psycopg import connect

from boto3 import client as boto3_client
from botocore.exceptions import ClientError

from spatialprofilingtoolbox.db.credentials import main_database_name
from spatialprofilingtoolbox.db.credentials import DBCredentials
from spatialprofilingtoolbox.db.credentials import retrieve_credentials_from_file
from spatialprofilingtoolbox.db.credentials import MissingKeysError
from spatialprofilingtoolbox.workflow.scripts.configure import _parse_s3_reference
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.standalone_utilities.log_formats import CustomFormatter

PREVIOUS_FILENAME = '.spt_last_used_config'


def parse_args():
    parser = argparse.ArgumentParser(
        prog='spt db interactive-uploader',
        description='Upload datasets. Options are selected interactively with prompts.'
    )
    parser.parse_args()


class QuitRequested(RuntimeError):
    """Raised when the user requests exiting the application."""
    def __init__(self):
        super().__init__('Quit requested.')


class InteractiveUploader:
    selected_database_config_file: str | None
    connectables: tuple[str, ...]
    credentials: DBCredentials | None
    selected_dataset_source: str | None
    sourceables: tuple[str, ...]
    drop_behavior: str | None
    existing_studies: tuple[str, ...]
    study_names_by_schema: dict[str, str]

    def __init__(self):
        self.selected_database_config_file = None
        self.connectables = ()
        self.selected_dataset_source = None
        self.sourceables = ()
        self.drop_behavior = None
        self.credentials = None
        self.existing_studies = None

    def start(self) -> None:
        self._initial_assessment_of_available_options()
        self._enter_upload_loop()

    def _initial_assessment_of_available_options(self) -> None:
        self.print('(Enter "q" to quit.)\n', style='message')
        self._assess_database_config_files()
        if self.selected_database_config_file is not None:
            self._assess_datasets()

    def _assess_database_config_files(self) -> None:
        home = expanduser('~')
        considered = [join(home, f) for f in listdir(home)] + listdir('.')
        filename_matches = tuple(filter(
            lambda filename: re.search('^\.spt_db.config', basename(filename)),
            filter(isfile, considered),
        ))
        if len(filename_matches) == 0:
            self.print('No database config files ', style='message', end='')
            self.print('(named like ', style='message', end='')
            self.print('.spt_db.config', style='popout', end='')
            self.print('...) were found in home directory or current working directory.', style='message')
            sys_exit(1)
        format_matches = tuple(filter(self._check_database_config_file_format, filename_matches))
        if len(format_matches) < len(filename_matches):
            print('')
        connectables = tuple(sorted(list(filter(self._check_connectability, format_matches))))
        if len(connectables) < len(format_matches):
            print('')
        self._report_validated_config_files(connectables)
        if len(connectables) == 1:
            file = connectables[0]
            self._select_config_file(file)
        else:
            self.connectables = connectables

    def _select_config_file(self, file: str) -> None:
        path, filename = split(file)
        self.print('Using ', style='message', end='')
        self.print(f'{path}{"/" if not path == "" else "./"}', style='fieldname', end='')
        self.print(f'{filename}', style='popout')
        print()
        self.selected_database_config_file = file
        self._record_selected_database_config_file(file)

    def _get_previous_database_config_file(self) -> str | None:
        file = join(expanduser('~'), PREVIOUS_FILENAME)
        if isfile(file):
            with open(file, 'rt', encoding='utf-8') as f:
                name = f.read()
            return name
        return None

    def _record_selected_database_config_file(self, filename: str) -> None:
        file = join(expanduser('~'), PREVIOUS_FILENAME)
        with open(file, 'wt', encoding='utf-8') as f:
            f.write(filename)
        self.credentials = retrieve_credentials_from_file(filename)

    def _report_validated_config_files(self, validated: tuple[str, ...]) -> None:
        self.print('Found database config files with correct format and validated credentials:', style='message')
        previous = self._get_previous_database_config_file()
        self._print_paths(validated, previous)
        print('')
        if previous is not None:
            self.print('Previously used marked with *.', 'message')
            print('')

    def _print_paths(self, paths: tuple[str, ...], indicated_item: str | None) -> None:
        pairs = [split(f) for f in paths]
        width = 2 + max([len(pair[0]) for pair in pairs])
        for i, (path, filename) in enumerate(pairs):
            if join(path, filename) == indicated_item:
                ordinal = f'*{i} '
            else:
                ordinal = f'{i} '
            self.print(ordinal.rjust(3), style='item', end='')
            self.print(f' {path}{"/" if not path == "" else "./"}'.rjust(width), style='fieldname', end='')
            self.print(f'{filename}', style='popout')

    def _check_database_config_file_format(self, filename: str) -> bool:
        try:
            retrieve_credentials_from_file(filename)
        except MissingKeysError as error:
            self.print(f'Warning: ', style='flag', end='')
            self.print(f'{filename}', style='popout', end='')
            self.print(f' is missing keys: ', style='message', end='')
            self.print(", ".join(list(error.missing)), style='item')
            return False
        return True

    def _check_connectability(self, file: str) -> bool:
        credentials = retrieve_credentials_from_file(file)
        try:
            with connect(
                dbname='postgres',
                host=credentials.endpoint,
                user=credentials.user,
                password=credentials.password,
            ) as _:
                return True
        except Exception:
            pass
        self.print(f'Warning: ', style='flag', end='')
        self.print(f'{file}', style='popout', end='')
        self.print(f' credentials are invalid or database ', style='message', end='')
        self.print('postgres', style='item', end='')
        self.print(f' does not exist.', style='message')
        return False

    def _assess_datasets(self) -> None:
        pass

    def _enter_upload_loop(self) -> None:
        quit_requested = False
        while not quit_requested:
            quit_requested = self._upload_loop()
        self.print('Exiting.', style='message')

    def _upload_loop(self) -> bool:
        for step in (
            self._solicit_and_ensure_database_selection,
            self._solicit_and_ensure_dataset_selection,
            self._solicit_intended_drop_behavior,
        ):
            try:
                step()
            except QuitRequested:
                return True
        try:
            proceed = self._solicit_confirmation_of_action()
        except QuitRequested:
            self.print('Dataset upload not scheduled.', 'flag')
            return True
        if proceed:
            self._do_specified_upload()
            return True
        return False

    def _solicit_and_ensure_database_selection(self) -> None:
        while self.selected_database_config_file is None:
            self.print('Select database config file', 'prompt', end='')
            previous_index = self._get_previous_index()
            if previous_index is not None:
                self.print(f' [default selection ', 'prompt', end='')
                self.print(f'{previous_index}', 'item', end='')
                self.print(']', 'prompt', end='')
            self.print(': ', 'prompt', end='')
            answer = input()
            print()
            if answer == 'q':
                raise QuitRequested
            if answer in ['', '\n'] and previous_index is not None:
                self._select_config_file(self.connectables[previous_index])
                continue
            try:
                index = int(answer)
            except ValueError:
                self.print('Enter a valid index', 'flag')
                continue
            if index < 0 or index >= len(self.connectables):
                self.print('Enter a valid index', 'flag')
                continue
            self._select_config_file(self.connectables[index])

    def _get_previous_index(self) -> int | None:
        previous = self._get_previous_database_config_file()
        if previous is None:
            return None
        for i, connectable in enumerate(self.connectables):
            if connectable == previous:
                return i
        return None

    def _solicit_and_ensure_dataset_selection(self) -> None:
        if len(self.sourceables) == 0:
            self._retrieve_dataset_sources()
        if len(self.sourceables) == 0:
            self.print('No dataset sources found, whether subdirectories of the form ', style='message', end='')
            self.print('../generated_artifacts/', style='popout', end='')
            self.print(' or folders in S3 bucket ', style='message', end='')
            self.print(f'{S3_BUCKET if S3_BUCKET else "(SPT_S3_BUCKET environment variable)"}', style='item', end='')
            self.print(' or folders in S3 bucket ', style='message')
            raise QuitRequested
        self._print_sources()
        while self.selected_dataset_source is None:
            answer = input('Select a dataset: ')
            if answer == 'q':
                raise QuitRequested
            try:
                index = int(answer)
            except ValueError:
                self.print('Enter a valid index.', 'flag')
                continue
            if index < 0 or index >= len(self.sourceables):
                self.print('Enter a valid index.', 'flag')
                continue
            self.selected_dataset_source = self.sourceables[index]

    def _print_sources(self) -> None:
        self.print('Available dataset sources:', style='message')
        for i, source in enumerate(self.sourceables):
            self.print(f'{i} '.rjust(3), style='item', end='')
            presence = self._determine_presence(source)
            self.print(f' {presence} '.rjust(19), style='fieldname', end='')
            self.print(f' {source}', style='dataset source')
        print()

    def _retrieve_study_name(self, source: str) -> str:
        study_name = None
        study_file = join(source, 'study.json')
        if isfile(study_file):
            with open(study_file, 'rt', encoding='utf-8') as file:
                study_name = json_loads(file.read())['Study name']
        if re.search('^s3://', source):
            resource = _parse_s3_reference(join(source, 'study.json'))
            client = boto3_client('s3')
            local_study_file = '_study.temp.json'
            client.download_file(resource.bucket, resource.get_key_string(), local_study_file)
            with open(local_study_file, 'rt', encoding='utf-8') as file:
                study_name = json_loads(file.read())['Study name']
        if study_name is None:
            raise ValueError(f'Could not find study name for given source: {source}')
        return study_name

    def _determine_presence(self, source: str) -> str:
        if self.existing_studies is None:
            with DBCursor(database_config_file=self.selected_database_config_file) as cursor:
                cursor.execute('SELECT study, schema_name FROM study_lookup;')
                name_schema = tuple(map(lambda row: (row[1], row[0]), cursor.fetchall()))
            self.study_names_by_schema = dict(name_schema)
            self.existing_studies = tuple(sorted(list(self.study_names_by_schema.values())))
        for study in self.existing_studies:
            if basename(source) == study:
                return 'present on remote'
            study_file = join(source, 'study.json')
            if isfile(study_file):
                with open(study_file, 'rt', encoding='utf-8') as file:
                    study_name = json_loads(file.read())['Study name']
                normal = re.sub('[ \-]', '_', study_name).lower()
                if normal == study:
                    return 'present on remote'
        return ''

    def _retrieve_dataset_sources(self) -> None:
        sources = []
        for root, dirs, _ in os_walk(abspath('.')):
            dirs[:] = [d for d in dirs if not d[0] == '.']
            if basename(root) == 'generated_artifacts':
                sources.append(root)
        if S3_BUCKET is not None:
            try:
                folders = []
                client = boto3_client('s3', region_name='us-east-1')
                paginator = client.get_paginator('list_objects_v2')
                pages = paginator.paginate(Bucket=S3_BUCKET, Delimiter='/', Prefix='')
                for page in pages:
                    for obj in page['CommonPrefixes']:
                        folders.append(obj['Prefix'].rstrip('/'))
            except ClientError:
                self.print('S3 client cannot connect to ', style='flag', end='')
                self.print(S3_BUCKET, style='item')
                raise QuitRequested
            uris = [f's3://{S3_BUCKET}/{f}' for f in folders]
            sources.extend(uris)
        self.sourceables = tuple(sources)

    def _solicit_intended_drop_behavior(self) -> None:
        behavior = None
        while behavior is None:
            self.print('Drop dataset before upload? [', 'prompt', end='')
            self.print('y', 'yes', end='')
            self.print('/', 'prompt', end='')
            self.print('n', 'no', end='')
            self.print('] (default no) ', 'prompt', end='')
            answer = input()
            print()
            if answer in ('y', 'Y', 'yes'):
                behavior = 'drop'
            if answer in ('n', 'N', 'no', ''):
                behavior = 'no drop'
        self.drop_behavior = behavior

    def _solicit_confirmation_of_action(self) -> bool:
        self._announce_plan()
        self.print('Proceed? [', 'prompt', end='')
        self.print('y', 'yes', end='')
        self.print('/', 'prompt', end='')
        self.print('n', 'no', end='')
        self.print('] (default no) ', 'prompt', end='')
        answer = input()
        print()
        if answer in ('y', 'Y', 'yes'):
            return True
        self.selected_dataset_source = None
        self.selected_database_config_file = None
        self.sourceables = ()
        return False

    def _announce_plan(self) -> None:
        self.print('Will upload dataset from', 'message')
        self.print(f'  {self.selected_dataset_source}', 'dataset source')
        self.print('to the database at', 'message')
        assert self.credentials is not None
        self.print(f'  {self.credentials.endpoint}', 'item', end='')
        self.print(f'  (from credentials ', 'message', end='')
        self.print(f'{self.selected_database_config_file}', 'popout', end='')
        self.print(f' )', 'message')
        if self.drop_behavior == 'drop':
            self.print('(The dataset will be dropped first, so the upload will be fresh.)', 'message')
        print()

    def _do_specified_upload(self) -> None:
        self._write_workflow_config()
        if self.drop_behavior == 'drop':
            self._drop_first()
        self._upload_commands()

    def _drop_first(self) -> None:
        study_name = self._retrieve_study_name(cast(str, self.selected_dataset_source))
        command = f'spt db drop --database-config-file={self.selected_database_config_file} --study-name="{study_name}"'
        self.print(f'  {command}', 'item')
        os_system(command)

    def _upload_commands(self) -> None:
        change = 'cd working_directory'
        configure = 'spt workflow configure --workflow="tabular import" --config-file=workflow.config'
        run = 'bash run.sh'
        commands = [change, configure, run]
        for c in commands:
            self.print(f'  {c}', 'item')
        print()
        os_system('; '.join(commands))

    def _write_workflow_config(self) -> None:
        config = ConfigParser()
        config['general'] = {'db_config_file': cast(str, self.selected_database_config_file)}
        config['tabular import'] = {'input_path': cast(str, self.selected_dataset_source)}
        w = 'working_directory'
        if not isdir(w):
            mkdir(w)
        with open(join(w, 'workflow.config'), 'w') as file:
            config.write(file)

    @staticmethod
    def print(message: str, style: str | None, end: str = '\n') -> None:
        codes = {
            None: '',
            'title': '\033[7;36m',
            'fieldname': '\033[100;97m',
            'message': '',
            'popout': CustomFormatter.magenta,
            'item': CustomFormatter.blue,
            'dataset source': CustomFormatter.yellow,
            'order': '\033[100;97m',
            'prompt': '',
            'flag': CustomFormatter.red,
            'no': CustomFormatter.red,
            'yes': CustomFormatter.green,
        }
        reset = CustomFormatter.reset
        print(f'{codes[style]}{message}{reset}', end=end)


def main():
    parse_args()
    gui = InteractiveUploader()
    try:
        gui.start()
    except KeyboardInterrupt:
        InteractiveUploader.print('\nCancelled by user request.', style='flag')


if __name__=='__main__':
    main()
