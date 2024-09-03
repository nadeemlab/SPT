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
from inspect import getfullargspec
from traceback import print_exception

from psycopg import connect
from psycopg import Connection as PsycopgConnection
from psycopg import Cursor as PsycopgCursor
from psycopg import Error as PsycopgError
from psycopg import OperationalError
from psycopg.errors import DuplicateDatabase
from attr import define

from spatialprofilingtoolbox.db.credentials import DBCredentials
from spatialprofilingtoolbox.db.credentials import get_credentials_from_environment
from spatialprofilingtoolbox.db.credentials import retrieve_credentials_from_file
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class DatabaseNotFoundError(ValueError):
    study: str

    def __init__(self, study: str):
        self.study = study
        super().__init__(self.verbalize())

    def verbalize(self) -> str:
        return f'Did not find database for study named: "{self.study}"'


class ConnectionProvider:
    """Simple wrapper of a database connection."""
    connection: PsycopgConnection

    def __init__(self, connection: PsycopgConnection):
        self.connection = connection

    def get_connection(self) -> PsycopgConnection:
        return self.connection

    def is_connected(self):
        try:
            connection = self.connection
            return connection is not None
        except AttributeError:
            return False


class DBConnection(ConnectionProvider):
    """
    Provides a psycopg Postgres database connection. Takes care of connecting and disconnecting.
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
        try:
            if study is not None:
                study_database = self._retrieve_study_database(credentials, study)
                credentials.update_database(study_database)
            super().__init__(self.make_connection(credentials))
        except PsycopgError as exception:
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
                raise DatabaseNotFoundError(study)
            return str(rows[0][0])

    @staticmethod
    def make_connection(credentials: DBCredentials) -> PsycopgConnection:
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
                try:
                    self.get_connection().commit()
                except OperationalError as error:
                    logger.warn('Connection was possibly interrupted by deliberate timeout. Stack trace:')
                    print_exception(type(error), error, error.__traceback__)
            self.get_connection().close()

    def __exit__(self, exception_type, exception_value, traceback):
        self.wrap_up_connection()


class DBCursor(DBConnection):
    """Context manager for shortcutting right to provision of a cursor."""
    cursor: PsycopgCursor

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_cursor(self) -> PsycopgCursor:
        return self.cursor

    def set_cursor(self, cursor: PsycopgCursor) -> None:
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
    except PsycopgError as _:
        return False


def retrieve_study_names(database_config_file: str | None) -> list[str]:
    with DBCursor(database_config_file=database_config_file) as cursor:
        cursor.execute('SELECT study FROM study_lookup;')
        rows = cursor.fetchall()
    return sorted([str(row[0]) for row in rows])


def get_specimen_names(cursor) -> list[str]:
    query = 'SELECT specimen FROM specimen_collection_process;'
    cursor.execute(query)
    rows = cursor.fetchall()
    return sorted([str(row[0]) for row in rows])


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


def retrieve_primary_study(database_config_file: str, component_study: str) -> str | None:
    studies = retrieve_study_names(database_config_file)
    for study in studies:
        with DBCursor(database_config_file=database_config_file, study=study) as cursor:
            query = 'SELECT COUNT(*) FROM study_component sc WHERE sc.component_study=%s ;'
            cursor.execute(query, (component_study,))
            count = tuple(cursor.fetchall())[0][0]
            if count == 1:
                return study
    return None


def create_database(database_config_file: str | None, database_name: str) -> None:
    if database_config_file is None:
        message = 'Data import requires a database configuration file.'
        logger.error(message)
        raise ValueError(message)
    credentials = retrieve_credentials_from_file(database_config_file)
    create_statement = f'CREATE DATABASE {database_name};'
    connection = connect(
        dbname='postgres',
        host=credentials.endpoint,
        user=credentials.user,
        password=credentials.password,
    )
    try:
        connection.autocommit = True
        try:
            with connection.cursor() as cursor:
                cursor.execute(create_statement)
        except DuplicateDatabase:
            logger.warning('Attempt to recreate existing database "%s".', database_name)
    finally:
        connection.close()


@define
class SimpleReadOnlyProvider:
    """State-holder for basic read-only one-time database data provider classes."""
    cursor: PsycopgCursor


class QueryCursor:
    """Dispatches calls to a provided handler class (most likely QueryHandler).
    The provided class' class methods require a cursor as first argument, which this dispatcher
    class (QueryCursor) newly provides on each invocation.
    This allows the user of QueryCursor to omit mention of the cursor.
    """
    query_handler: Type

    get_study_components: Callable
    retrieve_study_specifiers: Callable
    retrieve_study_handle: Callable
    get_channel_names: Callable
    get_number_cells: Callable
    get_study_summary: Callable
    get_cell_fractions_summary: Callable
    get_phenotype_symbols: Callable
    get_composite_phenotype_identifiers: Callable
    get_phenotype_criteria: Callable
    retrieve_signature_of_phenotype: Callable
    get_important_cells: Callable
    get_cells_data: Callable
    get_ordered_feature_names: Callable
    get_sample_names: Callable
    get_available_gnn: Callable
    get_study_findings: Callable
    get_study_gnn_plot_configurations: Callable
    has_umap: Callable
    is_public_collection: Callable

    def __init__(self, query_handler: Type):
        self.query_handler = query_handler
        methods = [method for method in dir(query_handler) if not method.startswith('__')]
        for method_name in methods:
            argument_names = getfullargspec(getattr(query_handler, method_name)).args
            if 'study' in argument_names:
                study_parameter_index = argument_names.index('study') - 2
            else:
                study_parameter_index = None
            def dispatched(
                *args,
                _method_name=method_name,
                _study_parameter_index=study_parameter_index,
                **kwargs,
            ):
                return self._query(
                    *args,
                    _method_name=_method_name,
                    _study_parameter_index=_study_parameter_index,
                    **kwargs,
                )
            setattr(self, method_name, dispatched)

    def _query(self,
        *args,
        _method_name: str = '',
        _study_parameter_index: int | None = None,
        **kwargs,
    ):
        method_function = getattr(self.query_handler, _method_name)
        if _study_parameter_index is None:
            with DBCursor() as cursor:
                return method_function(cursor, *args, **kwargs)
        else:
            with DBCursor(study=args[_study_parameter_index]) as cursor:
                return method_function(cursor, *args, **kwargs)
