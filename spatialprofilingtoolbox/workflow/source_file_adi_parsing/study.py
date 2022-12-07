import json

from ...db.source_file_parser_interface import SourceToADIParser
from ...standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)


class StudyParser(SourceToADIParser):
    def __init__(self, **kwargs):
        super(StudyParser, self).__init__(**kwargs)

    def cautious_insert(self, tablename, record, cursor, fields, no_primary=True):
        was_found, key = self.check_exists(tablename, record, cursor, fields, no_primary=no_primary)
        if was_found:
            logger.debug('"%s" %s already exists.', tablename, str(record))
        else:
            cursor.execute(
                self.generate_basic_insert_query(tablename, fields),
                record,
            )

    def parse(self, connection, fields, study_file):
        with open(study_file, 'rt') as study:
            study = json.loads(study.read())
            study_name = study['Study name']

        cursor = connection.cursor()

        record = (study['Study name'], study['Institution'])
        self.cautious_insert('study', record, cursor, fields)

        for p in study['People']:
            record = (p['Full name'], p['Surname'], p['Given name'], p['ORCID'])
            self.cautious_insert('research_professional', record, cursor, fields)

        record = (
            study['Study contact person']['Name'],
            study_name,
            study['Study contact person']['Contact reference'],
        )
        self.cautious_insert('study_contact_person', record, cursor, fields)

        collection = SourceToADIParser.get_measurement_study_name(study_name)
        measurement = SourceToADIParser.get_collection_study_name(study_name)
        data_analysis = SourceToADIParser.get_data_analysis_study_name(study_name)
        for substudy in [collection, measurement, data_analysis]:
            record = [study_name, substudy]
            self.cautious_insert('study_component', record, cursor, fields)

        for publication in study['Publications']:
            record = (
                publication['Title'],
                study_name,
                publication['Document type'],
                publication['Publisher'],
                publication['Date'],
                publication['URL'],
            )
            self.cautious_insert('publication', record, cursor, fields)

        for publication in study['Publications']:
            for ordinality, author in enumerate(publication['Authors']):
                record = (
                    author,
                    publication['Title'],
                    str(ordinality),
                )
                self.cautious_insert('author', record, cursor, fields)

        logger.info('Parsed records for study "%s".', study_name)
        connection.commit()
        cursor.close()
        return study_name
