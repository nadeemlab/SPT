"""CLI utility to stress the backend and database for testing."""
from argparse import ArgumentParser
from typing import cast
import re
from json import loads as json_loads

from requests import get as requests_get

from spatialprofilingtoolbox.db.scripts.interactive_uploader import InteractiveUploader as DatabaseSelector
Printer = DatabaseSelector

def parse_args():
    parser = ArgumentParser(
        prog='spt db load-testing',
        description='Test the backend, including load testing.'
    )
    parser.parse_args()


class QuitRequested(RuntimeError):
    """Raised when the user requests exiting the application."""
    def __init__(self):
        super().__init__('Quit requested.')


class LoadTester:
    database_selector: DatabaseSelector
    database_config_file: str
    api_url: str | None

    def __init__(self):
        self.database_selector = DatabaseSelector()
        self.api_url = None

    def start(self) -> None:
        self.database_selector._assess_database_config_files()
        self.database_selector._solicit_and_ensure_database_selection()
        self._start_tests()

    def _start_tests(self) -> None:
        try:
            self.database_selector._solicit_and_ensure_database_selection()
            self.database_config_file = cast(str, self.database_selector.selected_database_config_file)
            self._solicit_and_ensure_api_reachable()
        except QuitRequested:
            Printer.print('Quit requested.', style='flag')

    def _solicit_and_ensure_api_reachable(self):
        default_value = 'oncopathtk.org/api'
        while self.api_url is None:
            Printer.print('Select API server', 'prompt', end='')
            Printer.print(f' [default selection ', 'prompt', end='')
            Printer.print(f'{default_value}', 'item', end='')
            Printer.print(']', 'prompt', end='')
            Printer.print(': ', 'prompt', end='')
            answer = input()
            if answer == 'q':
                raise QuitRequested
            if answer in ['', '\n']:
                selection = default_value
            else:
                selection = answer
            metadata, validated = self._validate_api_server(selection)
            if validated:
                self.api_url = selection
                Printer.print('Selected server: ', end='', style='message')
                Printer.print(self.api_url, style='fieldname')
                Printer.print('API version:     ', end='', style='message')
                Printer.print(metadata['version'], style='fieldname')

    def _validate_api_server(self, server: str) -> tuple[dict, bool]:
        server = re.sub(r'^https?://', '', server)
        server = re.sub(r'/$', '', server)
        try:
            response = requests_get(f'http://{server}')
            if response.status_code != 200:
                Printer.print(f'This server is not reachable or unavailable (HTTP {response.status_code}).', style='flag')
            response = requests_get(f'http://{server}/openapi.json')
            if response.status_code != 200:
                Printer.print(f'This server does not advertisee an openapi.json description (HTTP {response.status_code}).', style='flag')
                return ({}, False)
        except ValueError as error:
            Printer.print(f'Something went wrong trying to reach this server.', style='flag')
            print(error)
            return ({}, False)
        except:
            Printer.print(f'Something went wrong with the connection while trying to reach this server.', style='flag')
            return ({}, False)
        data = json_loads(response.text)
        if not 'info' in data:
            Printer.print(f'"info" field missing from response.', style='flag')
            return ({}, False)
        if not 'version' in data['info']:
            Printer.print(f'"version" field missing from response.', style='flag')
            return ({}, False)
        version = data['info']['version']
        if not 'title' in data['info']:
            Printer.print(f'"title" field missing from response.', style='flag')
            return ({}, False)
        title = data['info']['title']
        expected = 'Single cell studies data API'
        if not title == expected:
            Printer.print(f'API server is not recognizable as the SPT application server. Got title: ', end='', style='message')
            Printer.print(title, style='item')
            return ({}, False)
        return ({'version': version}, True)

    # def _solicit_confirmation_of_action(self) -> bool:
    #     self._announce_plan()
    #     self.print('Proceed? [', 'prompt', end='')
    #     self.print('y', 'yes', end='')
    #     self.print('/', 'prompt', end='')
    #     self.print('n', 'no', end='')
    #     self.print('] (default no) ', 'prompt', end='')
    #     answer = input()
    #     print()
    #     if answer in ('y', 'Y', 'yes'):
    #         return True
    #     if answer == 'q':
    #         raise QuitRequested
    #     self.selected_dataset_source = None
    #     self.selected_database_config_file = None
    #     self.sourceables = ()
    #     return False

    # def _announce_plan(self) -> None:
    #     self.print('    Upload'.ljust(80), 'title')
    #     print()
    #     self.print('Will upload dataset from  '.ljust(26), 'message', end='')
    #     self.print(f'  {self.selected_dataset_source}', 'dataset source')
    #     self.print('to the database at'.ljust(26), 'message', end='')
    #     assert self.credentials is not None
    #     self.print(f'  {self.credentials.endpoint}', 'item', end='')
    #     self.print(f'  (from credentials ', 'message', end='')
    #     self.print(f'{self.selected_database_config_file}', 'popout', end='')
    #     self.print(f' )', 'message')
    #     if self.drop_behavior == 'drop':
    #         self.print('(The dataset will be dropped first, so the upload will be fresh.)', 'message')
    #     print()


def main():
    parse_args()
    gui = LoadTester()
    try:
        gui.start()
    except KeyboardInterrupt:
        Printer.print('\nCancelled by user request.', style='flag')


if __name__=='__main__':
    main()
