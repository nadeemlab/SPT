"""Source file parsing for overall study/project metadata."""
import json

from spatialprofilingtoolbox.db.source_file_parser_interface import SourceToADIParser
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class StudyParser(SourceToADIParser):
    """Parse source files containing study-level metadata."""

    def cautious_insert(self, tablename, record, cursor, no_primary=True):
        was_found, _ = self.check_exists(tablename, record, cursor, no_primary=no_primary)
        if was_found:
            logger.debug('"%s" %s already exists.', tablename, str(record))
        else:
            cursor.execute(self.generate_basic_insert_query(tablename), record)

    def parse(self, connection, study_file):
        with open(study_file, 'rt', encoding='utf-8') as study:
            study = json.loads(study.read())
            study_name = study['Study name']

        cursor = connection.cursor()

        record = (study['Study name'], study['Institution'])
        self.cautious_insert('study', record, cursor)

        for person in study['People']:
            record = (person['Full name'], person['Surname'],
                      person['Given name'], person['ORCID'])
            self.cautious_insert('research_professional',
                                 record, cursor)

        record = (
            study['Study contact person']['Name'],
            study_name,
            study['Study contact person']['Contact reference'],
        )
        self.cautious_insert('study_contact_person', record, cursor)

        collection = SourceToADIParser.get_measurement_study_name(study_name)
        measurement = SourceToADIParser.get_collection_study_name(study_name)
        data_analysis = SourceToADIParser.get_data_analysis_study_name(
            study_name)
        for substudy in [collection, measurement, data_analysis]:
            record = [study_name, substudy]
            self.cautious_insert('study_component', record, cursor)

        for publication in study['Publications']:
            record = (
                publication['Title'],
                study_name,
                publication['Document type'],
                publication['Publisher'],
                publication['Date'],
                publication['URL'],
            )
            self.cautious_insert('publication', record, cursor)

        for publication in study['Publications']:
            for ordinality, author in enumerate(publication['Authors']):
                record = (
                    author,
                    publication['Title'],
                    str(ordinality),
                )
                self.cautious_insert('author', record, cursor)

        logger.info('Parsed records for study "%s".', study_name)
        connection.commit()
        cursor.close()
        return study_name
