import importlib.resources
import re
import os
from os.path import getsize
import mmap
import io
from io import BytesIO as StringIO
import base64
import binascii

import psycopg2
import pandas as pd
import shapefile

from .log_formats import colorized_logger
logger = colorized_logger(__name__)

from .file_io import get_input_filenames_by_data_type
from .file_io import get_input_filename_by_identifier
from .file_io import get_outcomes_files
from .file_io import compute_sha256


class DataSkimmer:
    def __init__(self, endpoint, user, password, dataset_settings, dataset_design):
        try:
            self.connection = psycopg2.connect(
                dbname='pathstudies',
                user=user,
                password=password,
                host=endpoint,
            )
        except psycopg2.Error as e:
            logger.error('Failed to connect to database: %s', e.pgerror)
        self.dataset_settings = dataset_settings
        self.dataset_design = dataset_design

        with importlib.resources.path('spatialprofilingtoolbox', 'fields.tsv') as path:
            self.fields = pd.read_csv(path, sep='\t', na_filter=False)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.connection.close()

    def skim_initial_data(self):
        self.parse_outcomes()
        self.parse_cell_manifest_set()
        self.parse_channels_and_phenotypes()
        self.parse_cell_manifests()

    def normalize(self, string):
        string = re.sub('[ \-]', '_', string)
        string = string.lower()
        return string

    def get_field_names(self, tablename):
        fields = [
            field
            for i, field in self.fields.iterrows()
            if self.normalize(field['Table']) == self.normalize(tablename)
        ]
        fields_sorted = sorted(fields, key=lambda field: int(field['Ordinality']))
        return fields_sorted

    def generate_basic_insert_query(self, tablename):
        fields_sorted = self.get_field_names(tablename)
        query = (
            'INSERT INTO ' + tablename + ' (' + ', '.join([field['Name'] for field in fields_sorted]) + ') '
            'VALUES (' + ', '.join(['%s']*len(fields_sorted)) + ') '
            'ON CONFLICT DO NOTHING;'
        )
        return query

    def parse_outcomes(self):
        """
        Retrieve outcome data in the same way that the main workflows do, and parse
        records for:
        - subject
        - diagnosis
        """
        cursor = self.connection.cursor()

        def create_subject_record(sample_id):
            return (sample_id, '', '', '', '', '')

        def create_diagnosis_record(sample_id, result, column_name):
            return (sample_id, column_name, result, '', '')

        for outcomes_file in get_outcomes_files(self.dataset_settings):
            logger.debug('Considering %s', outcomes_file)
            outcomes = pd.read_csv(outcomes_file, sep='\t', na_filter=False)
            sample_ids = sorted(list(set(outcomes['Sample ID'])))
            logger.info('Saving %s subject records.', len(sample_ids))
            for sample_id in sample_ids:
                cursor.execute(
                    self.generate_basic_insert_query('subject'),
                    create_subject_record(sample_id),
                )
            logger.info('Saving %s diagnosis records.', outcomes.shape[0])
            for i, row in outcomes.iterrows():
                cursor.execute(
                    self.generate_basic_insert_query('diagnosis'),
                    create_diagnosis_record(
                        row['Sample ID'],
                        row[outcomes.columns[1]],
                        outcomes.columns[1]
                    ),
                )
        self.connection.commit()
        cursor.close()

    def parse_cell_manifest_set(self):
        """
        Retrieve the set of cell manifests (i.e. just the "metadata" for each source
        file), and parse records for:
        - specimen collection study
        - specimen collection process
        - specimen measurement study
        - specimen data measurement process
        - data file
        """
        file_metadata = pd.read_csv(self.dataset_settings.file_manifest_file, sep='\t')
        halo_data_type = 'HALO software cell manifest'
        cell_manifests = file_metadata[
            file_metadata['Data type'] == halo_data_type
        ]

        def create_specimen_collection_process_record(specimen, source, study):
            return (specimen, source, '', '', '', study)

        def create_specimen_data_measurement_process_record(
            identifier,
            specimen,
            study,
        ):
            return (identifier, specimen, '', '', study)

        def create_data_file_record(
            sha256_hash,
            file_name,
            file_format,
            contents_format,
            size,
            source_generation_process,
        ):
            return (
                sha256_hash,
                file_name,
                file_format,
                contents_format,
                size,
                source_generation_process,
            )

        project_handles = sorted(list(set(file_metadata['Project ID']).difference([''])))
        if len(project_handles) == 0:
            message = 'No "Project ID" values are supplied with the file manifest for this run.'
            logger.error(message)
            raise ValueError(message)
        if len(project_handles) > 1:
            message = 'Multiple "Project ID" values were supplied with the file manifest for this run. Using "%s".' % project_handles[0]
            logger.warning(message)
        project_handle = project_handles[0]
        collection_study = project_handle + ' - specimen collection'
        measurement_study = project_handle + ' - measurement'

        cursor = self.connection.cursor()
        cursor.execute(
            self.generate_basic_insert_query('specimen_collection_study'),
            (collection_study, '', '', '', '', ''),
        )
        cursor.execute(
            self.generate_basic_insert_query('specimen_measurement_study'),
            (measurement_study, 'Multiplexed imaging', '', 'HALO', '', ''),
        )

        for i, cell_manifest in cell_manifests.iterrows():
            logger.debug('Considering "%s" file "%s" .', halo_data_type, cell_manifest['File ID'])
            subject_id = cell_manifest['Sample ID']
            subspecimen_identifier = subject_id + ' subspecimen'
            cursor.execute(
                self.generate_basic_insert_query('specimen_collection_process'),
                create_specimen_collection_process_record(
                    subspecimen_identifier,
                    subject_id,
                    collection_study,
                ),
            )
            filename = get_input_filename_by_identifier(
                dataset_settings = self.dataset_settings,
                input_file_identifier = cell_manifest['File ID'],
            )
            sha256_hash = compute_sha256(filename)

            if 'SHA256' in cell_manifests.columns:
                if sha256_hash != cell_manifest['SHA256']:
                    logger.warning(
                        'Computed hash "%s" does not match hash supplied in file manifest, "%s", for file "%s".',
                        sha256_hash,
                        cell_manifest['SHA256'],
                        cell_manifest['File ID'],
                    )

            measurement_process_identifier = sha256_hash + ' measurement'
            cursor.execute(
                self.generate_basic_insert_query('specimen_data_measurement_process'),
                create_specimen_data_measurement_process_record(
                    measurement_process_identifier,
                    subspecimen_identifier,
                    measurement_study,
                ),
            )
            match = re.search('\.([a-zA-Z0-9]{1,8})$', cell_manifest['File name'])
            if match:
                file_format = match.groups(1)[0].upper()
            else:
                file_format = ''
            size = getsize(filename)
            cursor.execute(
                self.generate_basic_insert_query('data_file'),
                create_data_file_record(
                    sha256_hash,
                    cell_manifest['File name'],
                    file_format,
                    halo_data_type,
                    size,
                    measurement_process_identifier,
                ),
            )
        logger.info('Parsed records for %s cell manifests.', cell_manifests.shape[0])
        self.connection.commit()
        cursor.close()

    def is_integer(self, i):
        if isinstance(i, int):
            return True
        if re.match('^[0-9][0-9]*$', i):
            return True
        return False

    def get_next_integer_identifier(self, tablename, cursor, key_name = 'identifier'):
        cursor.execute('SELECT %s FROM %s;' % (key_name, tablename))
        try:
            identifiers = cursor.fetchall()
        except psycopg2.ProgrammingError as e:
            return 0
        known_integer_identifiers = [int(i[0]) for i in identifiers if self.is_integer(i[0])]
        if len(known_integer_identifiers) == 0:
            return 0
        else:
            return max(known_integer_identifiers) + 1

    def check_exists(self, tablename, record, cursor, no_primary=False):
        """
        Assumes that the first entry in records is a fiat identifier, omitted for 
        the purpose of checking pre-existence of the record.

        Returns pair:
        - was_found (bool)
        - key

        If no_primary = True, no fiat identifier column is assumed at all, and a key
        value of None is returned.
        """
        fields = self.get_field_names(tablename)
        primary = fields[0]['Name']
        if no_primary:
            primary = 'COUNT(*)'
            identifying_record = record
            identifying_fields = fields
        else:
            identifying_record = record[1:]
            identifying_fields = fields[1:]
        query = 'SELECT ' + primary + ' FROM ' + tablename + ' WHERE ' + ' AND '.join(
                [
                    field['Name'] + ' = %s '
                    for field in identifying_fields
                ]
            ) + ' ;'
        cursor.execute(query, tuple(identifying_record))
        if not no_primary:
            rows = cursor.fetchall()
            if len(rows) == 0:
                return [False, None]
            if len(rows) > 1:
                logger.warning('"%s" contains duplicates records.', tablename)
            key = rows[0][0]
            return [True, key]
        else:
            count = cursor.fetchall()[0][0]
            if count == 0:
                return [False, None]
            else:
                return [True, None]

    def parse_channels_and_phenotypes(self):
        """
        Retrieve the phenotype and channel metadata, and parse records for:
        - chemical species
        - biological marking system
        - data analysis study
        - cell phenotype
        - cell phenotype criterion
        """
        elementary_phenotypes_file = get_input_filename_by_identifier(
            dataset_settings = self.dataset_settings,
            input_file_identifier = 'Elementary phenotypes file',
        )
        composite_phenotypes_file = get_input_filename_by_identifier(
            dataset_settings = self.dataset_settings,
            input_file_identifier = 'Complex phenotypes file',
        )
        elementary_phenotypes = pd.read_csv(elementary_phenotypes_file, sep=',', na_filter=False)
        composite_phenotypes = pd.read_csv(composite_phenotypes_file, sep=',', na_filter=False)

        file_metadata = pd.read_csv(self.dataset_settings.file_manifest_file, sep='\t')
        project_handle = sorted(list(set(file_metadata['Project ID']).difference([''])))[0]
        data_analysis_study = project_handle + ' - data analysis'
        measurement_study = project_handle + ' - measurement'

        cursor = self.connection.cursor()

        identifier = self.get_next_integer_identifier('chemical_species', cursor)
        initial_value = identifier
        chemical_species_identifiers_by_symbol = {}
        for i, phenotype in elementary_phenotypes.iterrows():
            symbol = phenotype['Name']
            chemical_structure_class = phenotype['Indication type']
            record = (str(identifier), symbol, '', chemical_structure_class)
            was_found, key = self.check_exists('chemical_species', record, cursor)
            if not was_found:
                cursor.execute(
                    self.generate_basic_insert_query('chemical_species'),
                    record,
                )
                chemical_species_identifiers_by_symbol[symbol] = str(identifier)
                identifier = identifier + 1
            else:
                chemical_species_identifiers_by_symbol[symbol] = key
                logger.debug(
                    '"chemical_species" %s already exists.',
                    str([''] + list(record[1:])),
                )
        self.chemical_species_identifiers_by_symbol = chemical_species_identifiers_by_symbol
        logger.info('Saved %s chemical species records.', identifier - initial_value)

        identifier = self.get_next_integer_identifier('biological_marking_system', cursor)
        initial_value = identifier
        for i, phenotype in elementary_phenotypes.iterrows():
            symbol = phenotype['Name']
            record = (
                str(identifier),
                str(chemical_species_identifiers_by_symbol[symbol]),
                '',
                '',
                measurement_study,
            )
            was_found, key = self.check_exists('biological_marking_system', record, cursor)
            if not was_found:
                cursor.execute(
                    self.generate_basic_insert_query('biological_marking_system'),
                    record,
                )
                identifier = identifier + 1
            else:
                logger.debug(
                    '"biological_marking_system" %s already exists.',
                    str([''] + list(record[1:])),
                )
        logger.info('Saved %s biological marking system records.', identifier - initial_value)

        cursor.execute(
            self.generate_basic_insert_query('data_analysis_study'),
            (data_analysis_study, ),
        )

        identifier = self.get_next_integer_identifier('cell_phenotype', cursor)
        initial_value = identifier
        cell_phenotype_identifiers_by_symbol = {}
        number_criterion_records = 0
        for i, phenotype in composite_phenotypes.iterrows():
            symbol = phenotype['Name']
            record = (str(identifier), symbol, '')
            was_found, key = self.check_exists('cell_phenotype', record, cursor)
            if not was_found:
                cursor.execute(
                    self.generate_basic_insert_query('cell_phenotype'),
                    record,
                )
                cell_phenotype_identifiers_by_symbol[symbol] = str(identifier)
                identifier = identifier + 1
            else:
                cell_phenotype_identifiers_by_symbol[symbol] = key
                logger.debug(
                    '"cell_phenotype" %s already exists.',
                    str([''] + list(record[1:])),
                )
            positive_markers = set(str(phenotype['Positive markers']).split(';')).difference([''])
            negative_markers = set(str(phenotype['Negative markers']).split(';')).difference([''])
            missing = positive_markers.union(negative_markers).difference(
                chemical_species_identifiers_by_symbol.keys()
            )
            if len(missing) > 0:
                logger.warning(
                    'Markers %s are part of phenotype %s but do not represent any known "chemical_species". This marker is skipped.',
                    missing,
                    record,
                )
            signature = [
                ('positive', chemical_species_identifiers_by_symbol[m])
                for m in set(positive_markers).difference(missing)
            ] + [
                ('negative', chemical_species_identifiers_by_symbol[m])
                for m in set(negative_markers).difference(missing)
            ]
            for polarity, chemical_species_identifier in signature:
                record = (
                    cell_phenotype_identifiers_by_symbol[phenotype['Name']],
                    chemical_species_identifier,
                    polarity,
                    data_analysis_study,
                )
                was_found, _ = self.check_exists('cell_phenotype_criterion', record, cursor, no_primary=True)
                if not was_found:
                    cursor.execute(
                        self.generate_basic_insert_query('cell_phenotype_criterion'),
                        record,
                    )
                    number_criterion_records += 1
                else:
                    logger.debug(
                        '"cell_phenotype_criterion" %s already exists.',
                        str(record),
                    )
        logger.info('Saved %s cell phenotype records.', identifier - initial_value)
        logger.info('Saved %s cell phenotype criterion records.', number_criterion_records)

        logger.info(
            'Parsed records implied by "%s" and "%s".',
            elementary_phenotypes_file,
            composite_phenotypes_file,
        )
        self.connection.commit()
        cursor.close()

    def get_number_known_cells(self, sha256_hash, cursor):
        query = (
            'SELECT COUNT(*) '
            'FROM histological_structure_identification '
            'WHERE data_source = %s ;'
        )
        cursor.execute(query, (sha256_hash,))
        count = cursor.fetchall()[0][0]
        return count

    def get_polygon_coordinates(self, cell):
        columns = self.dataset_design.get_box_limit_column_names()
        extrema = [cell[c] for c in columns]
        xmin, xmax, ymin, ymax = extrema
        return [
            [xmin, ymin],
            [xmin, ymax],
            [xmax, ymax],
            [xmin, ymax],
        ]

    def create_shape_file(self, cell):
        shp = StringIO()
        shx = StringIO()
        dbf = StringIO()
        points = self.get_polygon_coordinates(cell)
        points = points + [points[-1]]
        w = shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shapefile.POLYGON)
        w.field('name', 'C')
        w.poly([points])
        w.record()
        w.close()
        contents = shp.getvalue()
        encoded = base64.b64encode(shp.getvalue())
        ascii_representation = encoded.decode('utf-8')
        return ascii_representation

    def parse_cell_manifests(self):
        """
        Retrieve each cell manifest, and parse records for:
        - histological structure identification
        - histological structure
        - shape file
        - expression quantification
        """
        file_metadata = pd.read_csv(self.dataset_settings.file_manifest_file, sep='\t')
        halo_data_type = 'HALO software cell manifest'
        cell_manifests = file_metadata[
            file_metadata['Data type'] == halo_data_type
        ]
        recognized_channel_symbols = self.dataset_design.get_elementary_phenotype_names()
        missing_channel_symbols = set(
            self.chemical_species_identifiers_by_symbol.keys()
        ).difference(recognized_channel_symbols)
        if len(missing_channel_symbols) > 0:
            logger.warning(
                'Cannot find channel metadata for %s .',
                str(missing_channel_symbols),
            )
        channel_symbols = set(
            self.chemical_species_identifiers_by_symbol.keys()
        ).difference(missing_channel_symbols)

        cursor = self.connection.cursor()
        histological_structure_identifier_index = self.get_next_integer_identifier('histological_structure', cursor)
        shape_file_identifier_index = self.get_next_integer_identifier('shape_file', cursor)
        for i, cell_manifest in cell_manifests.iterrows():
            logger.debug(
                'Considering contents of "%s" file "%s".',
                halo_data_type,
                cell_manifest['File ID'],
            )
            filename = get_input_filename_by_identifier(
                dataset_settings = self.dataset_settings,
                input_file_identifier = cell_manifest['File ID'],
            )
            sha256_hash = compute_sha256(filename)
            cells = pd.read_csv(filename, sep=',', na_filter=False).drop_duplicates()
            count = self.get_number_known_cells(sha256_hash, cursor)
            if count > 0 and count != cells.shape[0]:
                logger.warning(
                    ('Found %s cells but %s already known from data source file "%s". '
                    ' You may need to drop bad cell records from '
                    'histological_structure_identification table, or check the source '
                    'data file\'s integrity. For now, skipping this source file.'),
                    cells.shape[0],
                    count,
                    sha256_hash,
                )
                continue
            elif count == cells.shape[0]:
                logger.debug(
                    ('Already found exactly %s cells recorded from data source '
                    ' file "%s". Skipping this file.'
                    ),
                    count,
                    sha256_hash,
                )
                continue
            elif count == 0:
                chunk_size = 1000
                for start in range(0, cells.shape[0], chunk_size):
                    batch_cells = cells.iloc[start:start + chunk_size]
                    records = {
                        'histological_structure' : [],
                        'shape_file' : [],
                        'histological_structure_identification' : [],
                        'expression_quantification' : [],
                    }
                    intensities = {
                        symbol : self.dataset_design.get_combined_intensity(batch_cells, symbol)
                        for symbol in channel_symbols
                    }
                    for j, cell in batch_cells.iterrows():
                        histological_structure_identifier = str(histological_structure_identifier_index)
                        histological_structure_identifier_index += 1
                        shape_file_identifier = str(shape_file_identifier_index)
                        shape_file_identifier_index += 1
                        shape_file_contents = self.create_shape_file(cell)
                        records['histological_structure'].append((
                            histological_structure_identifier,
                            'cell',
                        ))
                        records['shape_file'].append((
                            shape_file_identifier,
                            'ESRI Shapefile SHP',
                            shape_file_contents,
                        ))
                        records['histological_structure_identification'].append((
                            histological_structure_identifier,
                            sha256_hash,
                            shape_file_identifier,
                            '\\N',
                            '',
                            '',
                            '',
                        ))
                        for symbol in channel_symbols:
                            target = self.chemical_species_identifiers_by_symbol[symbol]
                            quantity = intensities[symbol][j]
                            if quantity in [None, '']:
                                continue
                            discrete_value = cell[self.dataset_design.get_feature_name(symbol)]
                            records['expression_quantification'].append((
                                histological_structure_identifier,
                                target,
                                str(quantity),
                                '',
                                '',
                                'positive' if discrete_value == 1 else 'negative',
                                '',
                            ))

                    tablenames = [
                        'histological_structure',
                        'shape_file',
                        'histological_structure_identification',
                        'expression_quantification',
                    ]
                    for tablename in tablenames:
                        values_file_contents = '\n'.join([
                            '\t'.join(r) for r in records[tablename]
                        ]).encode('utf-8')
                        with mmap.mmap(-1, len(values_file_contents)) as mm:
                            mm.write(values_file_contents)
                            mm.seek(0)
                            cursor.copy_from(mm, tablename)
            logger.info('Parsed records for %s cells from "%s".', cells.shape[0], sha256_hash)

        self.connection.commit()
        cursor.close()

    def skim_final_data(self, ):
        pass
        # two cohort feature assocation test
        # feature specification
        # feaure specifier
        # diagnostic selection criterion

