import sqlite3
import time

from .log_formats import colorized_logger

logger = colorized_logger(__name__)


class WaitingDatabaseContextManager:
    """
    A wrapper over a sqlite database execution that just waits until the database is
    available, using a fixed-wait-time loop. It is designed for usage with Python's
    "with ... as" construct.
    """
    def __init__(self, uri, seconds=5.0):
        """
        Args:
            uri (str):
                The SQL database Uniform Resource Identifier (URI).
            seconds (float):
                Number of seconds to wait until retrying a given execution, in case the
                database is locked.
        """
        self.uri = uri
        self.seconds = seconds

    def __enter__(self):
        self.connection = sqlite3.connect(self.uri)
        self.cursor = self.connection.cursor()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.connection.commit()
        self.cursor.close()
        self.connection.close()

    def execute_commit(self, cmd):
        """
        Executes a SQL command and commits the connection.

        Args:
            cmd (str):
                The SQL command to execute.

        Returns:
            The result of the `fetchall()` sqlite function.
        """
        return self.execute(cmd, commit=True)

    def execute(self, cmd, commit=False):
        """
        Executes a SQL command and, by default, does not commit the connection.

        Args:
            cmd (str):
                The SQL command to execute.
            commit (bool):
                Whether to commit.

        Returns:
            The result of the `fetchall()` sqlite function.
        """
        while(True):
            try:
                result = self.cursor.execute(cmd).fetchall()
                if commit:
                    self.connection.commit()
                break
            except sqlite3.OperationalError as e:
                if str(e) == 'database is locked':
                    logger.debug('Database %s was locked, waiting %s seconds to retry: %s', self.uri, self.seconds, cmd)
                    time.sleep(self.seconds)
                else:
                    raise e
        return result

    def commit(self):
        """
        Explicitly commits the connection.
        """
        while(True):
            try:
                self.connection.commit()
                break
            except sqlite3.OperationalError as e:
                if str(e) == 'database is locked':
                    logger.debug('Database %s was locked, waiting %s seconds to retry committing.', self.uri, self.seconds)
                    time.sleep(self.seconds)
                else:
                    raise e
