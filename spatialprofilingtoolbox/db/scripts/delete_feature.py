"""CLI utility to drop one feature (values, specification, specifiers) from the database"""

import argparse
from typing import cast

from attr import define
from pandas import DataFrame

from spatialprofilingtoolbox.db.database_connection import get_and_validate_database_config
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.standalone_utilities.log_formats import CustomFormatter

def parse_args():
    parser = argparse.ArgumentParser(
        prog='spt db delete-feature',
        description='Drop one quantitative feature, including all specifiers and values.'
    )
    parser.add_argument(
        '--specification',
        dest='specification',
        help='The feature specification identifier, typically a decimal integer string.',
        required=False,
    )
    add_argument(parser, 'database config')
    parser.add_argument(
        '--study-name',
        dest='study_name',
        help='The name of the study for which the feature was computed.',
        required=True
    )
    return parser.parse_args()


@define
class InteractiveFeatureDropper:
    study: str
    database_config_file: str
    specification: str | None
    known_specifications: tuple[str, ...] | None = None
    specifiers: tuple[str, ...] | None = None
    method: str | None = None

    def start(self):
        specified = self._solicit_specification()
        if not specified:
            return
        proceed = self._solicit_confirmation()
        if not proceed:
            self._print('Cancelling by user request.', 'flag')
            return
        self._perform_deletion()

    def _solicit_specification(self) -> bool:
        specifications = self._get_specifications()
        if specifications is None:
            return False
        columns = ['Specification', 'Specifier', 'Ordinality', 'Method']
        df = DataFrame(specifications, columns=columns)
        self.known_specifications = tuple(df['Specification'])

        self._print(f'   Feature specifications for study "{self.study}"   ', 'title')
        for method, df1 in df.groupby('Method'):
            self._print(str(method), 'method')
            for specification, df2 in df1.groupby('Specification'):
                one_liner = self._form_one_liner(df2)
                self._print(str(specification).rjust(3), 'specification', end='')
                self._print(': ', None, end='')
                self._print(one_liner, 'specifiers')
            print('')

        if self.specification is not None:
            if not self._check_valid_specification():
                self._print('Specification ', 'message', end='')
                self._print(self.specification, 'specification', end='')
                self._print(' does not exist.', 'message')
                return False
        else:
            self._print('Choose specification: ', 'message', end='')
            try:
                self.specification = input()
                print()
            except KeyboardInterrupt:
                self._print('Cancelled by user request.', 'flag')
                return False
        if not self._check_valid_specification():
            self._print(self.specification, 'specification', end='')
            self._print(' is not a valid specification', 'message')
            return False

        _df = df[df['Specification'] == self.specification].copy()
        _df['Int ordinality'] = df['Ordinality'].apply(int)
        self.specifiers = tuple(_df.sort_values(by='Int ordinality')['Specifier'])
        self.method = str(tuple(_df['Method'])[0])
        return True

    def _print(self, message: str, style: str | None, end: str = '\n') -> None:
        codes = {
            None: '',
            'title': '\033[7;36m',
            'method': '\033[100;97m',
            'message': '',
            'specification': CustomFormatter.magenta,
            'specifiers': CustomFormatter.blue,
            'order': '\033[100;97m',
            'prompt': '',
            'flag': CustomFormatter.red,
            'no': CustomFormatter.red,
            'yes': CustomFormatter.green,
        }
        reset = CustomFormatter.reset
        print(f'{codes[style]}{message}{reset}', end=end)

    def _check_valid_specification(self) -> bool:
        if self.specification in cast(tuple[str, ...], self.known_specifications):
            return True
        return False

    def _form_one_liner(self, df: DataFrame) -> str:
        df['Int ordinality'] = df['Ordinality'].apply(int)
        df = df.sort_values(by='Int ordinality')
        specifiers = tuple(df['Specifier'])
        return ', '.join([str(s) for s in specifiers])

    def _solicit_confirmation(self) -> bool:
        self._announce_plan()
        self._print('Proceed? [', 'prompt', end='')
        self._print('y', 'yes', end='')
        self._print('/', 'prompt', end='')
        self._print('n', 'no', end='')
        self._print('] ', 'prompt', end='')
        answer = input()
        print()
        if answer in ('y', 'Y', 'yes'):
            return True
        return False

    def _announce_plan(self) -> None:
        self._print('Deleting specification ', 'message', end='')
        self._print(cast(str, self.specification), 'specification', end='')
        self._print(':', 'message')
        for i, specifier in enumerate(cast(tuple[str, ...], self.specifiers)):
            self._print(str(i + 1).rjust(8) + ' ', 'order', end='')
            self._print(' ', None, end='')
            self._print(specifier, 'specifiers')
        self._print('method'.rjust(8) + ' ', 'order', end='')
        self._print(' ', None, end='')
        method = cast(str, self.method)
        self._print(method[0:min(len(method), 100)] + ' ...', 'specifiers')

    def _perform_deletion(self):
        self._print('Proceed to delete specification ', 'message', end='')
        self._print(self.specification, 'specification', end='')
        self._print('.', 'message')
        with DBCursor(database_config_file=self.database_config_file, study=self.study) as cursor:
            param = (self.specification,)
            cursor.execute('DELETE FROM quantitative_feature_value WHERE feature=%s ;', param)
            cursor.execute('DELETE FROM feature_specifier WHERE feature_specification=%s ;', param)
            cursor.execute('DELETE FROM feature_specification WHERE identifier=%s ;', param)
        self._print('Done.', 'message')

    def _get_specifications(self) -> tuple[tuple[str, ...], ...] | None:
        with DBCursor(database_config_file=self.database_config_file, study=self.study) as cursor:
            cursor.execute('''
            SELECT fs.identifier, fsp.specifier, fsp.ordinality, fs.derivation_method
            FROM feature_specification fs
            JOIN feature_specifier fsp ON fsp.feature_specification=fs.identifier ;
            ''')
            rows = tuple(tuple(str(x) for x in row) for row in cursor.fetchall())
        if len(rows) == 0:
            self._print('No feature specification for study ', 'flag', end='')
            self._print(self.study, None)
            return None
        return rows


def main():
    args = parse_args()
    database_config_file = get_and_validate_database_config(args)
    study = args.study_name
    specification = args.specification
    gui = InteractiveFeatureDropper(study, database_config_file, specification)
    gui.start()


if __name__=='__main__':
    main()
