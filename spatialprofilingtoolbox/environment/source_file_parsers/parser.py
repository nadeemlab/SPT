import psycopg2
import re
import enum
from enum import Enum
from enum import auto

from ..logging.log_formats import colorized_logger
logger = colorized_logger(__name__)


class DBBackend(Enum):
    POSTGRES = auto()


class SourceFileSemanticParser:
    def __init__(self, **kwargs):
        pass

    def parse(self):
        pass

    def get_placeholder(self):
        placeholder = '%s'
        return placeholder

    def normalize(self, string):
        string = re.sub('[ \-]', '_', string)
        string = string.lower()
        return string

    def get_field_names(self, tablename, fields):
        fields = [
            field
            for i, field in fields.iterrows()
            if self.normalize(field['Table']) == self.normalize(tablename)
        ]
        fields_sorted = sorted(fields, key=lambda field: int(field['Ordinality']))
        fields_sorted = [f['Name'] for f in fields_sorted]
        return fields_sorted

    def format_value(self, v):
        if type(v) is tuple:
            raise ValueError('Not formatting tuple value, only atomic: %s' % str(v))
        if type(v) is list:
            raise ValueError('Not formatting list value, only atomic: %s' % str(v))
        if type(v) is int:
            return str(v)
        if type(v) is float:
            return str(v)
        if type(v) is str:
            if '"' in v:
                raise ValueError('Need more sophisticated quoting; encountered " character in string value: %s' % v)
            return '"' + v + '"'
        if '"' in str(v):
            raise ValueError('Need more sophisticated quoting; encountered " character in string value: %s' % v)
        return '"' + str(v) + '"'

    def generate_basic_insert_query(self, tablename, fields, not_equal_to_record=None):
        fields_sorted = self.get_field_names(tablename, fields)
        if not not_equal_to_record is None:
            str_formatted = [self.format_value(v) for v in not_equal_to_record]
            handle_duplicates = (
                'WHERE NOT EXISTS ('
                'SELECT * FROM ' + tablename + ' '
                'WHERE ' + ', '.join([
                    fields_sorted[i] + '=' + str_formatted[i]
                    for i in range(len(fields_sorted))
                ]) + ''
                ' ) '
            )
        else:
            handle_duplicates = 'ON CONFLICT DO NOTHING '
        query = (
            'INSERT INTO ' + tablename + ' (' + ', '.join(fields_sorted) + ') '
            'VALUES (' + ', '.join([self.get_placeholder()]*len(fields_sorted)) + ') '
            + handle_duplicates + ' ;' 
        )
        return query

    def is_integer(self, i):
        if isinstance(i, int):
            return True
        if re.match('^[0-9][0-9]*$', i):
            return True
        return False

    def get_next_integer_identifier(self, tablename, cursor, key_name = 'identifier'):
        cursor.execute('SELECT %s FROM %s;' % (key_name, tablename))
        try:
            identifiers = cursor.fetchall()
        except psycopg2.ProgrammingError as e:
            return 0
        known_integer_identifiers = [int(i[0]) for i in identifiers if self.is_integer(i[0])]
        if len(known_integer_identifiers) == 0:
            return 0
        else:
            return max(known_integer_identifiers) + 1

    def check_exists(self, tablename, record, cursor, fields, no_primary=False):
        """
        Assumes that the first entry in records is a fiat identifier, omitted for 
        the purpose of checking pre-existence of the record.

        Returns pair:
        - was_found (bool)
        - key

        If no_primary = True, no fiat identifier column is assumed at all, and a key
        value of None is returned.
        """
        fields = self.get_field_names(tablename, fields)
        primary = fields[0]['Name']
        if no_primary:
            primary = 'COUNT(*)'
            identifying_record = record
            identifying_fields = fields
        else:
            identifying_record = record[1:]
            identifying_fields = fields[1:]
        query = 'SELECT ' + primary + ' FROM ' + tablename + ' WHERE ' + ' AND '.join(
                [
                    field['Name'] + ' = %s ' % self.get_placeholder()
                    for field in identifying_fields
                ]
            ) + ' ;'
        cursor.execute(query, tuple(identifying_record))
        if not no_primary:
            rows = cursor.fetchall()
            if len(rows) == 0:
                return [False, None]
            if len(rows) > 1:
                logger.warning('"%s" contains duplicates records.', tablename)
            key = rows[0][0]
            return [True, key]
        else:
            count = cursor.fetchall()[0][0]
            if count == 0:
                return [False, None]
            else:
                return [True, None]
