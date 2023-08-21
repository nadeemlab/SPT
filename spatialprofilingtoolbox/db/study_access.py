"""Convenience accessors of study-related small data / metadata."""

from typing import cast
import re
from spatialprofilingtoolbox.db.simple_method_cache import simple_instance_method_cache

from spatialprofilingtoolbox.workflow.common.export_features import ADIFeatureSpecificationUploader
from spatialprofilingtoolbox.db.exchange_data_formats.study import (
    StudyContact,
    DataRelease,
    Publication,
    Institution,
    Assay,
    CountsSummary,
    StudyComponents,
    StudyHandle,
    StudySummary,
    Context,
    Products,
)
from spatialprofilingtoolbox.db.simple_query_patterns import GetSingleResult
from spatialprofilingtoolbox.db.cohorts import get_sample_cohorts
from spatialprofilingtoolbox.db.database_connection import SimpleReadOnlyProvider
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class StudyAccess(SimpleReadOnlyProvider):
    """Provide study-related metadata."""

    def get_study_summary(self, study: str) -> StudySummary:
        components = self.get_study_components(study)
        counts_summary = self._get_counts_summary(components)
        contact = self._get_contact(study)
        institution = self._get_institution(study)
        data_release = self._get_data_release(study)
        publication = self._get_publication(study)
        assay = self._get_assay(components.measurement)
        sample_cohorts = get_sample_cohorts(self.cursor, study)
        return StudySummary(
            context=Context(institution=institution, assay=assay, contact=contact),
            products=Products(data_release=data_release, publication=publication),
            counts=counts_summary,
            cohorts=sample_cohorts,
        )

    def get_study_components(self, study_name: str) -> StudyComponents:
        substudy_tables = {
            'collection': 'specimen_collection_study',
            'measurement': 'specimen_measurement_study',
            'analysis': 'data_analysis_study',
        }
        substudies = {}
        for key, tablename in substudy_tables.items():
            self.cursor.execute(f'''
            SELECT ss.name FROM {tablename} ss
            JOIN study_component sc ON sc.component_study=ss.name
            WHERE sc.primary_study=%s
            ;
            ''', (study_name,))
            name = [
                row[0] for row in self.cursor.fetchall()
                if not self._is_secondary_substudy(row[0])
            ][0]
            substudies[key] = name
        return StudyComponents(**substudies)

    @staticmethod
    def _is_secondary_substudy(substudy: str) -> bool:
        is_fractions = bool(re.search('phenotype fractions', substudy))
        is_proximity_calculation = bool(re.search('proximity calculation', substudy))
        descriptor = ADIFeatureSpecificationUploader.ondemand_descriptor()
        is_ondemand_calculation = bool(re.search(descriptor, substudy))
        return is_fractions or is_proximity_calculation or is_ondemand_calculation

    def get_study_handles(self) -> list[StudyHandle]:
        handles: list[StudyHandle] = []
        self.cursor.execute('SELECT study_specifier FROM study;')
        rows = self.cursor.fetchall()
        for row in rows:
            handle = str(row[0])
            display_name_detail = self._get_publication_summary_text(handle)
            handles.append(StudyHandle(handle=handle, display_name_detail=display_name_detail))
        return handles

    def _get_publication_summary_text(self, study: str) -> str:
        query = '''
        SELECT publisher, date_of_publication
        FROM publication
        WHERE study=%s AND document_type=\'Article\'
        ;
        '''
        row = GetSingleResult.row(self.cursor, query=query, parameters=(study,),)
        if row is None:
            publication_summary_text = ''
        else:
            publisher, publication_date = row
            year_match = re.search(r'^\d{4}', publication_date)
            if year_match:
                year = year_match.group()
                publication_summary_text = f'{publisher} {year}'
            else:
                publication_summary_text = publisher
        return publication_summary_text

    def _get_contact(self, study: str) -> StudyContact:
        row = GetSingleResult.row(
            self.cursor,
            query='''
            SELECT name, contact_reference
            FROM study_contact_person
            WHERE study=%s
            ''',
            parameters=(study,),
        )
        row = cast(tuple, row)
        return StudyContact(
            name=row[0],
            email_address=row[1] if self._rough_check_is_email(row[1]) else ''
        )

    @staticmethod
    def _rough_check_is_email(string):
        return not re.match('^[A-Za-z0-9+_.-]+@([^ ]+)$', string) is None

    def _get_data_release(self, study: str) -> DataRelease:
        query = '''
        SELECT publisher, internet_reference, date_of_publication
        FROM publication
        WHERE study=%s AND document_type=\'Dataset\'
        ;
        '''
        row = GetSingleResult.row(self.cursor, query=query, parameters=(study,),)
        row = cast(tuple, row)
        return DataRelease(**dict(zip(['repository', 'url', 'date'], row)))

    def _get_publication(self, study: str) -> Publication:
        query = '''
        SELECT title, internet_reference, date_of_publication
        FROM publication
        WHERE study=%s AND document_type=\'Article\'
        ;
        '''
        row = GetSingleResult.row(self.cursor, query=query, parameters=(study,),)
        if row is None:
            row = ('', '', '')
        title, url, date = row
        first_author_name = GetSingleResult.string(
            self.cursor,
            query='''
            SELECT person FROM author
            WHERE publication=%s
            ORDER BY regexp_replace(ordinality, '[^0-9]+', '', 'g')::int
            ;
            ''',
            parameters=(title,),
            or_else_value='',
        )
        return Publication(title=title, url=url, first_author_name=first_author_name, date=date)

    def _get_assay(self, measurement_study: str) -> Assay:
        name = GetSingleResult.string(
            self.cursor,
            query='SELECT assay FROM specimen_measurement_study WHERE name=%s;',
            parameters=(measurement_study,),
        )
        return Assay(name=name)

    @simple_instance_method_cache(maxsize=1000)
    def get_number_cells(self, specimen_measurement_study: str) -> int:
        logger.debug('Querying for number of cells in "%s".', specimen_measurement_study)
        query = '''
        SELECT count(*)
        FROM histological_structure_identification hsi
        JOIN histological_structure hs ON hsi.histological_structure = hs.identifier
        JOIN data_file df ON hsi.data_source = df.sha256_hash
        JOIN specimen_data_measurement_process sdmp ON df.source_generation_process = sdmp.identifier
        WHERE sdmp.study=%s AND hs.anatomical_entity='cell'
        ;
        '''
        return GetSingleResult.integer(
            self.cursor,
            query=query,
            parameters=(specimen_measurement_study,),
        )

    def _get_number_channels(self, specimen_measurement_study: str) -> int:
        query = '''
        SELECT count(*)
        FROM biological_marking_system bms
        WHERE bms.study=%s
        ;
        '''
        return GetSingleResult.integer(
            self.cursor,
            query=query,
            parameters=(specimen_measurement_study,),
        )

    def _get_number_specimens(self, specimen_measurement_study: str) -> int:
        return GetSingleResult.integer(
            self.cursor,
            query='''
            SELECT count(DISTINCT specimen)
            FROM specimen_data_measurement_process
            WHERE study=%s
            ;
            ''',
            parameters=(specimen_measurement_study,),
        )

    def _get_number_composite_phenotypes(self, analysis_study: str) -> int:
        return GetSingleResult.integer(
            self.cursor,
            query='''
            SELECT count(DISTINCT cell_phenotype)
            FROM cell_phenotype_criterion
            WHERE study=%s
            ;
            ''',
            parameters=(analysis_study,),
        )

    def _get_counts_summary(self, components: StudyComponents) -> CountsSummary:
        return CountsSummary(
            specimens=self._get_number_specimens(components.measurement),
            cells=self.get_number_cells(components.measurement),
            channels=self._get_number_channels(components.measurement),
            composite_phenotypes=self._get_number_composite_phenotypes(components.analysis),
        )

    def _get_institution(self, study: str) -> Institution:
        name = GetSingleResult.string(
            self.cursor,
            query='SELECT institution FROM study WHERE study_specifier=%s; ',
            parameters=(study,),
        )
        return Institution(name=name)

    def get_study_from_specimen(self, specimen: str) -> str:
        query = '''
        SELECT sc.primary_study
        FROM specimen_collection_process scp
        JOIN study_component sc ON sc.component_study=scp.study
        WHERE scp.specimen=%s
        ;
        '''
        study = GetSingleResult.string(
            self.cursor,
            query=query,
            parameters=(specimen,),
        )
        return study
