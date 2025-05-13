
import re
from importlib.resources import as_file
from importlib.resources import files
from contextlib import closing
from decimal import Decimal

from pandas import read_csv
from pandas import DataFrame
from networkx import MultiDiGraph
from networkx import topological_sort
from sqlite3 import connect
from sqlite3 import Cursor as SQLiteCursor
from psycopg import Cursor as PsycopgCursor
from attrs import define

from spatialprofilingtoolbox.db.database_connection import DBConnection
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.verbose_sql_execution import _retrieve_script

feature_computation_tables = (
    'Quantitative feature value',
)

feature_specification_tables = (
    'Feature specification',
    'Feature specifier',
)

big_tables = (
    'Histological structure',
    'Shape file',
    'Histological structure identification',
    'Expression quantification',
)

@define
class EdgeData:
    foreign_table: str
    foreign_key: str
    name: str


class SQLiteBuilder:
    """
    Creates a SQLite dump of the metadata elements (small data) of a given `scstudies` dataset
    located inside the application database.
    """
    connection: DBConnection
    include_feature_values: bool
    include_feature_specifications: bool

    def __init__(self, connection: DBConnection, no_feature_values: bool=False, no_feature_specifications: bool=False):
        self.connection = connection
        self.schema_graph = None
        self.include_feature_values = not no_feature_values
        self.include_feature_specifications = not no_feature_specifications

    def get_dump(self, study: str) -> bytes:
        with closing(connect(':memory:')) as db:
            with closing(db.cursor()) as cursor:
                self._infuse_schema(cursor)
                self._save_study(cursor, study)
            db.commit()
            serialization = db.serialize()
        return serialization

    def _split_on_unquoted(self, string: str, delimiter: str, quote_characters: str) -> tuple[str, ...]:
        inside_quote = False
        start = 0
        tokens = []
        for i, c in enumerate(string):
            if c in quote_characters:
                inside_quote = not inside_quote
                continue
            if c == delimiter and not inside_quote:
                token = string[start:i]
                tokens.append(token)
                start = i + 1
        return tuple(tokens)

    def _infuse_schema(self, cursor: SQLiteCursor) -> None:
        schema = _retrieve_script(('schema.sql', ''), None, 'adiscstudies', quiet=True)
        for statement in self._split_on_unquoted(schema, ';', "'"):
            statement = re.sub(r'^[\s\n]*COMMENT ON ', r'-- COMMENT ON ', statement)
            cursor.execute(f'{statement} ;')

    def _get_safe_table_insert_order(self) -> tuple[str]:
        G = self._get_schema_graph()
        return tuple(reversed(tuple(topological_sort(G))))

    def _get_primary_table_handle(self, field_record) -> str:
        return field_record['Table']

    def _get_edge_data(self, field_record) -> EdgeData:
        return EdgeData(field_record['Foreign table'], field_record['Foreign key'], field_record['Name'])

    def _get_fields(self) -> DataFrame:
        with as_file(files('adiscstudies').joinpath('fields.tsv')) as path:
            fields = read_csv(path, sep='\t', keep_default_na=False)
        return fields

    def _get_schema_graph(self) -> MultiDiGraph:
        G = MultiDiGraph()
        fields = self._get_fields()
        for _, row in fields.iterrows():
            edge_data = self._get_edge_data(row)
            n1 = self._get_primary_table_handle(row)
            n2 = edge_data.foreign_table
            if n2 == '':
                continue
            if n1 in self._omittable_tables() or n2 in self._omittable_tables():
                continue
            G.add_edge(
                n1,
                n2,
                name = edge_data.name,
                foreign_key = edge_data.foreign_key,
            )
        return G

    def _omittable_tables(self) -> tuple[str, ...]:
        omittables = list(big_tables)
        if not self.include_feature_values:
            omittables.extend(list(feature_computation_tables))
        if not self.include_feature_specifications:
            omittables.extend(list(feature_specification_tables))
        return tuple(omittables)

    def _save_study(self, target: SQLiteCursor, study: str) -> None:
        tables = self._get_safe_table_insert_order()
        with DBCursor(connection=self.connection, study=study) as source:
            for table in tables:
                table_name = self._normalize(table)
                self._copy_records(source, target, table_name)

    def _copy_records(self, source: PsycopgCursor, target: SQLiteCursor, table_name: str) -> None:
        query = f'SELECT * FROM {table_name};'
        source.execute(query)
        for row in source.fetchall():
            slots = ', '.join(['?'] * len(row))
            insert = f'INSERT INTO {table_name} VALUES ({slots});'
            target.execute(insert, self._clean_row(row))

    def _clean_row(self, row: tuple) -> tuple:
        return tuple(map(self._clean_entry, row))

    def _clean_entry(self, entry):
        if isinstance(entry, Decimal):
            return float(entry)
        return entry

    @staticmethod
    def _normalize(name):
        return re.sub(r'[ \-]', '_', name).lower()
