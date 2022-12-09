import re

from ...standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)


class SampleStratificationCreator:
    insert_assignment = '''
    INSERT INTO sample_strata (identifier, sample, temporal_position_relative_to_interventions, diagnosis)
    VALUES ( %s, %s, %s, %s )
    ;
    '''

    @staticmethod
    def create_sample_stratification(connection):
        cursor = connection.cursor()
        logger.info('Creating sample (specimen) stratification based on diagnoses and/or interventions.')

        specimens = SampleStratificationCreator.get_specimen_ids(cursor)
        identifiers = {}
        strata_count = 0
        for specimen in specimens:
            interventional_position, diagnostic_state = SampleStratificationCreator.get_verbalization_of_interventional_diagnosis(specimen, cursor)
            key = (interventional_position, diagnostic_state)
            if key == ('', ''):
                continue
            if not key in identifiers:
                strata_count = strata_count = 1
                identifiers[key] = strata_count
            record = (identifiers[key], specimen, interventional_position, diagnostic_state)
            cursor.execute(SampleStratificationCreator.insert_assignment, record)

        logger.info('Assigned %s samples to an annotated stratum.', len(specimens))
        cursor.close()

    @staticmethod
    def get_verbalization_of_interventional_diagnosis(specimen, cursor):
        subject, extraction_date = SampleStratificationCreator.get_source_event(specimen, cursor)
        interventions = SampleStratificationCreator.get_interventions(subject, cursor)
        diagnoses = SampleStratificationCreator.get_diagnoses(subject, cursor)
        return [
            SampleStratificationCreator.get_verbalization_of_interventional_position(interventions, extraction_date),
            SampleStratificationCreator.get_verbalization_of_diagnostic_state(extraction_date, diagnoses),
        ]

    @staticmethod
    def get_verbalization_of_interventional_position(interventions, extraction_date):
        if len(interventions) > 0:
            valuation_function = SampleStratificationCreator.get_date_valuation([i[1] for i in interventions] + [extraction_date])
            sequence = sorted(interventions + [('source extraction', extraction_date)], key=lambda x: valuation_function(x[1]))
            extraction_index = [index for index, event in enumerate(sequence) if event[0] == 'source extraction'][0]
            earlier_events = [event for index, event in enumerate(sequence) if index < extraction_index]
            later_events = [event for index, event in enumerate(sequence) if index > extraction_index]
            if len(earlier_events) == 0:
                verbalization = 'Before %s' % later_events[0][0]
            if len(earlier_events) > 0:
                if len(later_events) == 0:
                    verbalization = 'After %s' % earlier_events[-1][0]
                else:
                    verbalization = 'Between %s, %s' % (earlier_events[-1][0], later_events[0][0])
            return verbalization
        else:
            return ''

    @staticmethod
    def get_verbalization_of_diagnostic_state(extraction_date, diagnoses):
        valuation_function = SampleStratificationCreator.get_date_valuation([extraction_date] + [d[1] for d in diagnoses])
        sequence = sorted(diagnoses, key=lambda x: valuation_function(x[1]))
        influenced_diagnoses = []
        for diagnosis in sequence:
            if valuation_function(diagnosis[1]) >= valuation_function(extraction_date):
                influenced_diagnoses.append(diagnosis)
        if len(influenced_diagnoses) > 0:
            diagnosis = influenced_diagnoses[0]
            return diagnosis[0]
        else:
            return ''

    @staticmethod
    def get_date_valuation(dates):

        def iso_valuation(date):
            parts = date.split('-')
            if len(parts) < 2:
                raise Exception('Only one hyphen-delimited part, not an ISO 8601 date.')
            numeric_parts = []
            for i, part in enumerate(parts):
                stripped = part.lstrip('0')
                if stripped.isnumeric():
                    numeric_parts.append(int(stripped))
                else:
                    raise Exception('Part %s of date is not numeric.' % part)
            return tuple(numeric_parts)

        def numeric_valuation(date):
            return float(date)

        def timepoint_extractor(date):
            match = re.search('timepoint [\d]+$', date)
            if match:
                return match.group()
            else:
                raise Exception('Not marked with an explicit timepoint.')

        for valuation in [iso_valuation, numeric_valuation, timepoint_extractor]:
            if all([SampleStratificationCreator.is_convertible(date, valuation) for date in dates]):
                return valuation
        logger.warning('No order could be determined among: %s', dates)
        return None

    @staticmethod
    def is_convertible(string, valuation):
        try:
            conversion = valuation(string)
            return True
        except:
            return False

    @staticmethod
    def get_specimen_ids(cursor):
        cursor.execute('SELECT specimen FROM specimen_collection_process;')
        rows = cursor.fetchall()
        return [specimen for specimen in rows]

    @staticmethod
    def get_source_event(specimen, cursor):
        cursor.execute('SELECT source, extraction_date FROM specimen_collection_process WHERE specimen=%s ;', (specimen,))
        rows = cursor.fetchall()
        return rows[0]

    @staticmethod
    def get_interventions(subject, cursor):
        cursor.execute('SELECT specifier, date FROM intervention WHERE subject=%s ;', (subject,))
        rows = cursor.fetchall()
        return rows

    @staticmethod
    def get_diagnoses(subject, cursor):
        cursor.execute('SELECT condition, result, date_of_evidence FROM diagnosis WHERE subject=%s ;', (subject,))
        rows = cursor.fetchall()
        return rows
        return [(' '.join([row[0], row[1]]), row[2]) for row in rows]
