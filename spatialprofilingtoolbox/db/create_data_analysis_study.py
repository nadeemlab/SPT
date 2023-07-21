"""Functions to create, insert, and check for a data analysis study in the database."""
import re
import datetime

from psycopg2.extensions import connection as Psycopg2Connection

# from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


# def insert_new_data_analysis_study(
#     database_connection_maker: DatabaseConnectionMaker,
#     study_name: str,
#     specifier: str
# ) -> str:
#     """Insert a new data analysis study into the database and return its derived name."""
#     timestring = str(datetime.datetime.now())
#     name = f'{study_name} : {specifier} : {timestring}'
#     connection = database_connection_maker.get_connection()
#     cursor = connection.cursor()
#     cursor.execute('''
#         INSERT INTO data_analysis_study(name)
#         VALUES (%s) ;
#         INSERT INTO study_component(primary_study, component_study)
#         VALUES (%s, %s) ;
#     ''', (name, study_name, name))
#     cursor.close()
#     connection.commit()
#     logger.info('Inserted data analysis study: "%s"', name)
#     return name


# def data_analysis_study_exists(
#     database_connection_maker: DatabaseConnectionMaker,
#     study: str,
#     indicator: str
# ) -> bool:
#     """Check if a specific data analysis study exists in the database."""
#     connection = database_connection_maker.get_connection()
#     cursor = connection.cursor()
#     cursor.execute('''
#         SELECT das.name
#         FROM data_analysis_study das
#         JOIN study_component sc
#             ON sc.component_study=das.name
#         WHERE sc.primary_study=%s
#     ;
#     ''', (study,))
#     names: list[str] = [row[0] for row in cursor.fetchall()]
#     return any(re.search(indicator, name) for name in names)


class DataAnalysisStudyFactory:
    """Creates and retrieves custom data analysis studies in the database."""
    connection: Psycopg2Connection
    study: str
    specifier: str
    name: str | None

    def __init__(self, connection, study: str, specifier: str):
        self.connection = connection
        self.study = study
        self.specifier = specifier
        self._retrieve_existing_study()
        if self._already_exists():
            raise ValueError(f'Data analysis study "{self.name}" already exists.')

    def _retrieve_existing_study(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT das.name
            FROM data_analysis_study das
            JOIN study_component sc
                ON sc.component_study=das.name
            WHERE sc.primary_study=%s
        ;
        ''', (self.study,))
        names: list[str] = [row[0] for row in cursor.fetchall()]
        matches = [name for name in names if re.search(self.specifier, name)]
        if len(matches) > 0:
            self.name = matches[0]
        else:
            self.name = None

    def _already_exists(self):
        return self.name is not None

    def create(self) -> str:
        timestring = str(datetime.datetime.now())
        name = f'{self.study} : {self.specifier} : {timestring}'
        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT INTO data_analysis_study(name)
            VALUES (%s) ;
            INSERT INTO study_component(primary_study, component_study)
            VALUES (%s, %s) ;
        ''', (name, self.study, name))
        cursor.close()
        self.connection.commit()
        logger.info('Inserted data analysis study: "%s"', name)
        return name
