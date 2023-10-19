"""
A context manager from accessing the backend SPT database, from inside library
functions.
"""
import time
from os.path import exists
from os.path import abspath
from os.path import expanduser
from typing import Type
from typing import Callable

from psycopg2 import connect
from psycopg2.extensions import connection as Connection
from psycopg2.extensions import cursor as Psycopg2Cursor
from psycopg2 import Error as Psycopg2Error
from psycopg2 import OperationalError
from attr import define

from spatialprofilingtoolbox.db.credentials import DBCredentials
from spatialprofilingtoolbox.db.credentials import get_credentials_from_environment
from spatialprofilingtoolbox.db.credentials import retrieve_credentials_from_file
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class ConnectionProvider:
    """Simple wrapper of a database connection."""
    connection: Connection

    def __init__(self, connection: Connection):
        self.connection = connection

    def get_connection(self):
        return self.connection

    def is_connected(self):
        try:
            connection = self.connection
            return connection is not None
        except AttributeError:
            return False


class DBConnection(ConnectionProvider):
    """Provides a psycopg2 Postgres database connection. Takes care of connecting and disconnecting.
    """
    autocommit: bool

    def __init__(self,
        database_config_file: str | None = None,
        autocommit: bool=True,
        study: str | None = None,
    ):
        if database_config_file is not None:
            credentials = retrieve_credentials_from_file(database_config_file)
        else:
            credentials = get_credentials_from_environment()

        # try:
        #     self.make_connection(credentials)
        # except Psycopg2Error:
        #     logger.warning('Using "postgres" database as backup.')
        #     credentials = credentials.update_database('postgres')
        #     try:
        #         self.make_connection(credentials)
        #     except Psycopg2Error:
        #         raise ValueError('Could not connect to database "postgres".')

        try:
            if study is not None:
                study_database = self._retrieve_study_database(credentials, study)
                credentials.update_database(study_database)
            super().__init__(self.make_connection(credentials))
        except Psycopg2Error as exception:
            message = 'Failed to connect to database: %s, %s'
            logger.error(message, credentials.endpoint, credentials.database)
            raise exception
        self.autocommit = autocommit

    def _retrieve_study_database(self, credentials: DBCredentials, study: str) -> str:
        with connect(
            dbname=credentials.database,
            host=credentials.endpoint,
            user=credentials.user,
            password=credentials.password,
        ) as connection:
            cursor = connection.cursor()
            cursor.execute('SELECT database_name FROM study_lookup WHERE study=%s', (study,))
            rows = cursor.fetchall()
            if len(rows) == 0:
                raise ValueError('Did not find database for study "%s"', study)
            return str(rows[0][0])

    @staticmethod
    def make_connection(credentials: DBCredentials) -> Connection:
        logger.debug('Using credentials: host=%s database=%s user=%s', credentials.endpoint, credentials.database, credentials.user)
        return connect(
            dbname=credentials.database,
            host=credentials.endpoint,
            user=credentials.user,
            password=credentials.password,
        )

    def __enter__(self):
        return self.get_connection()

    def wrap_up_connection(self):
        if self.is_connected():
            if self.autocommit:
                self.get_connection().commit()
            self.get_connection().close()

    def __exit__(self, exception_type, exception_value, traceback):
        self.wrap_up_connection()


class DBCursor(DBConnection):
    """Context manager for shortcutting right to provision of a cursor."""
    cursor: Psycopg2Cursor

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_cursor(self) -> Psycopg2Cursor:
        return self.cursor

    def set_cursor(self, cursor: Psycopg2Cursor) -> None:
        self.cursor = cursor

    def __enter__(self):
        self.set_cursor(self.get_connection().cursor())
        return self.get_cursor()

    def __exit__(self, exception_type, exception_value, traceback):
        if self.is_connected():
            self.get_cursor().close()
        self.wrap_up_connection()


def get_and_validate_database_config(args):
    if args.database_config_file:
        config_file = abspath(expanduser(args.database_config_file))
        if not exists(config_file):
            raise FileNotFoundError(
                f'Need to supply valid database config filename: {config_file}')
        return config_file
    raise ValueError('Could not parse CLI argument for database config.')


def wait_for_database_ready():
    while True:
        try:
            if _check_database_is_ready():
                break
        except OperationalError:
            logger.debug('Database is not ready.')
            time.sleep(2.0)
    logger.info('Database is ready.')


def _check_database_is_ready() -> bool:
    try:
        with DBCursor() as cursor:
            cursor.execute('SELECT * FROM study_lookup;')
            _ = cursor.fetchall()
            return True
    except Psycopg2Error as _:
        return False


def retrieve_study_names(database_config_file: str | None) -> list[str]:
    with DBCursor(database_config_file=database_config_file) as cursor:
        cursor.execute('SELECT study FROM study_lookup;')
        rows = cursor.fetchall()
    return sorted([row[0] for row in rows])


def get_specimen_names(cursor) -> list[str]:
    query = 'SELECT specimen FROM specimen_collection_process;'
    cursor.execute(query)
    rows = cursor.fetchall()
    return sorted([row[0] for row in rows])


def retrieve_study_from_specimen(database_config_file: str | None, specimen: str) -> str:
    studies = retrieve_study_names(database_config_file)
    study = None
    for _study in studies:
        with DBCursor(database_config_file=database_config_file, study=_study) as cursor:
            specimens = get_specimen_names(cursor)
            if specimen in specimens:
                study = _study
                break
    if study is None:
        message = 'Could not retrieve study from specimen "%s".'
        logger.error(message, specimen)
        raise ValueError(message, specimen)
    return study


def create_database(database_config_file: str | None, database_name: str) -> None:
    if database_config_file is None:
        message = 'Data import requires a database configuration file.'
        logger.error(message)
        raise ValueError(message)
    credentials = retrieve_credentials_from_file(database_config_file)
    create_statement = 'CREATE DATABASE %s;' % database_name
    connection = connect(
        dbname='postgres',
        host=credentials.endpoint,
        user=credentials.user,
        password=credentials.password,
    )
    try:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(create_statement)
    finally:
        connection.close()


@define
class SimpleReadOnlyProvider:
    """State-holder for basic read-only one-time database data provider classes."""
    cursor: Psycopg2Cursor


class QueryCursor:
    """Dispatches calls to a provided handler class (most likely QueryHandler).
    The provided class' class methods require a cursor as first argument, which this dispatcher
    class (QueryCursor) newly provides on each invocation.
    This allows the user of QueryCursor to omit mention of the cursor.
    """
    query_handler: Type

    get_study_components: Callable
    retrieve_study_handles: Callable
    get_channel_names: Callable
    get_number_cells: Callable
    get_study_summary: Callable
    get_cell_fractions_summary: Callable
    get_phenotype_symbols: Callable
    get_phenotype_symbols_all_studies: Callable
    get_composite_phenotype_identifiers: Callable
    get_phenotype_criteria: Callable
    get_channel_names_all_studies: Callable
    retrieve_signature_of_phenotype: Callable
    get_umaps_low_resolution: Callable
    get_umap: Callable
    get_cggnn_metrics: Callable
    get_important_cells: Callable

    def __init__(self, query_handler: Type):
        self.query_handler = query_handler
        methods = [method for method in dir(query_handler) if not method.startswith('__')]
        for method_name in methods:
            def dispatched(*args, _method_name=method_name, **kwargs):
                return self._query(*args, _method_name=_method_name, **kwargs)
            setattr(self, method_name, dispatched)

    def _query(self, *args, _method_name: str='', **kwargs):
        method_function = getattr(self.query_handler, _method_name)
        with DBCursor() as cursor:
            return method_function(cursor, *args, **kwargs)
