import sqlite3
import time

from .log_formats import colorized_logger

logger = colorized_logger(__name__)


class WaitingDatabaseContextManager:
    """
    Wrapper to sqlite database execution that just waits until available.
    Designed for usage with Python's "with ... as" construct.
    """
    def __init__(self, uri):
        self.uri = uri

    def __enter__(self):
        self.connection = sqlite3.connect(self.uri)
        self.cursor = self.connection.cursor()
        return self

    def execute_commit(self, cmd):
        return self.execute(cmd, commit=True)

    def execute(self, cmd, commit=False):
        while(True):
            try:
                result = self.cursor.execute(cmd).fetchall()
                if commit:
                    self.connection.commit()
                break
            except sqlite3.OperationalError as e:
                if str(e) == 'database is locked':
                    seconds = 0.25
                    logger.debug('Database was locked, waiting %s seconds.', seconds)
                    time.sleep(seconds)
                else:
                    raise e
        return result

    def commit(self):
        self.connection.commit()

    def __exit__(self, exception_type, exception_value, traceback):
        self.cursor.close()
        self.connection.close()
