"""CLI utility to review and annotate result submissions."""
from argparse import ArgumentParser
from typing import cast
from os import environ as os_environ

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.credentials import retrieve_credentials_from_file
from spatialprofilingtoolbox.db.scripts.interactive_uploader import InteractiveUploader as DatabaseSelector
Printer = DatabaseSelector

def parse_args():
    parser = ArgumentParser(
        prog='spt db review-submissions',
        description='Review and annotates results/findings submissions.'
    )
    parser.parse_args()


class QuitRequested(RuntimeError):
    """Raised when the user requests exiting the application."""
    def __init__(self):
        super().__init__('Quit requested.')



class Reviewer:
    database_selector: DatabaseSelector

    def __init__(self):
        self.database_selector = DatabaseSelector()

    def start(self) -> None:
        self.database_selector._assess_database_config_files()
        self.database_selector._solicit_and_ensure_database_selection()
        self._start_review_loop()

    def _start_review_loop(self) -> None:
        try:
            database_config_file = cast(str, self.database_selector.selected_database_config_file)
            credentials = retrieve_credentials_from_file(database_config_file)
            os_environ['SINGLE_CELL_DATABASE_HOST'] = credentials.endpoint
            os_environ['SINGLE_CELL_DATABASE_USER'] = credentials.user
            os_environ['SINGLE_CELL_DATABASE_PASSWORD'] = credentials.password
            self._print_findings()
            self._accept_commands()
        except QuitRequested:
            Printer.print('Quit requested.', style='flag')

    def _print_findings(self) -> None:
        Printer.print('findings')

    def _accept_commands(self) -> None:
        Printer.print('commands')

        # with DBCursor(study=study) as cursor:
        #     OnDemandComputationsDropper.drop_features(cursor, [specification], just_features=True, verbose=False)

        # Printer.print('Cleaning up test example computed feature... ', end='', style='item')

    # def _print_numbers_and_names(self, rows) -> None:
    #     for row in rows:
    #         Printer.print(row[0].ljust(30), end='', style='fieldname')
    #         Printer.print(' ', end='', style='message')
    #         Printer.print(str(row[1]).rjust(6), style='message')


def main():
    parse_args()
    gui = Reviewer()
    try:
        gui.start()
    except KeyboardInterrupt:
        Printer.print('\nCancelled by user request.', style='flag')


if __name__=='__main__':
    main()
