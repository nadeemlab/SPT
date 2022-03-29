import pandas as pd

from ..file_io import get_input_filename_by_identifier
from .parser import SourceFileSemanticParser
from ..log_formats import colorized_logger
logger = colorized_logger(__name__)


class ChannelsPhenotypesParser(SourceFileSemanticParser):
    def __init__(self, **kwargs):
        super(ChannelsPhenotypesParser, self).__init__(**kwargs)

    def parse(self, connection, fields, dataset_settings, dataset_design):
        """
        Retrieve the phenotype and channel metadata, and parse records for:
        - chemical species
        - biological marking system
        - data analysis study
        - cell phenotype
        - cell phenotype criterion
        """
        elementary_phenotypes_file = get_input_filename_by_identifier(
            dataset_settings = dataset_settings,
            input_file_identifier = 'Elementary phenotypes file',
        )
        composite_phenotypes_file = get_input_filename_by_identifier(
            dataset_settings = dataset_settings,
            input_file_identifier = 'Complex phenotypes file',
        )
        elementary_phenotypes = pd.read_csv(elementary_phenotypes_file, sep=',', na_filter=False)
        composite_phenotypes = pd.read_csv(composite_phenotypes_file, sep=',', na_filter=False)

        file_metadata = pd.read_csv(dataset_settings.file_manifest_file, sep='\t')
        project_handle = sorted(list(set(file_metadata['Project ID']).difference([''])))[0]
        data_analysis_study = project_handle + ' - data analysis'
        measurement_study = project_handle + ' - measurement'

        cursor = connection.cursor()

        identifier = self.get_next_integer_identifier('chemical_species', cursor)
        initial_value = identifier
        chemical_species_identifiers_by_symbol = {}
        for i, phenotype in elementary_phenotypes.iterrows():
            symbol = phenotype['Name']
            chemical_structure_class = phenotype['Indication type']
            record = (str(identifier), symbol, '', chemical_structure_class)
            was_found, key = self.check_exists('chemical_species', record, cursor, fields)
            if not was_found:
                cursor.execute(
                    self.generate_basic_insert_query('chemical_species', fields),
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
            was_found, key = self.check_exists('biological_marking_system', record, cursor, fields)
            if not was_found:
                cursor.execute(
                    self.generate_basic_insert_query('biological_marking_system', fields),
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
            self.generate_basic_insert_query('data_analysis_study', fields),
            (data_analysis_study, ),
        )

        identifier = self.get_next_integer_identifier('cell_phenotype', cursor)
        initial_value = identifier
        cell_phenotype_identifiers_by_symbol = {}
        number_criterion_records = 0
        for i, phenotype in composite_phenotypes.iterrows():
            symbol = phenotype['Name']
            record = (str(identifier), symbol, '')
            was_found, key = self.check_exists('cell_phenotype', record, cursor, fields)
            if not was_found:
                cursor.execute(
                    self.generate_basic_insert_query('cell_phenotype', fields),
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
                was_found, _ = self.check_exists('cell_phenotype_criterion', record, cursor, fields, no_primary=True)
                if not was_found:
                    cursor.execute(
                        self.generate_basic_insert_query('cell_phenotype_criterion', fields),
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
        connection.commit()
        cursor.close()
        return chemical_species_identifiers_by_symbol
