"""Source file parsing for imaging/feature-assessment channel metadata."""
import pandas as pd

from spatialprofilingtoolbox.db.source_file_parser_interface import SourceToADIParser
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


def infer_common_marking_mechanism(channels):
    mechanisms = list(set(row['Marking mechanism'] for i, row in channels.iterrows()))
    if len(mechanisms) > 1:
        logger.warning('Encountered multiple marking mechanisms: %s', mechanisms)
    if len(mechanisms) == 1:
        mechanism = mechanisms[0]
    else:
        mechanism = ''
        logger.warning('Failed to infer marking mechanism.')
    logger.info('Inferred marking mechanism: %s', mechanism)
    return mechanism


class ChannelsPhenotypesParser(SourceToADIParser):
    """Source file parsing for imaging/feature-assessment channel metadata."""
    def parse(self,
              connection,
              channels_file,
              phenotypes_file,
              study_name):
        """
        Retrieve the phenotype and channel metadata, and parse records for:
        - chemical species
        - biological marking system
        - data analysis study
        - cell phenotype
        - cell phenotype criterion
        """
        channels = pd.read_csv(
            channels_file, sep=',', na_filter=False, dtype=str)
        phenotypes = pd.read_csv(
            phenotypes_file, sep=',', na_filter=False, dtype=str)

        data_analysis_study = SourceToADIParser.get_data_analysis_study_name(study_name)
        measurement_study = SourceToADIParser.get_measurement_study_name(study_name)

        cursor = connection.cursor()

        identifier = self.get_next_integer_identifier('chemical_species', cursor)
        initial_value = identifier
        chemical_species_identifiers_by_symbol = {}
        for _, phenotype in channels.iterrows():
            symbol = phenotype['Name']
            chemical_structure_class = phenotype['Target structure class']
            record = (
                str(identifier),
                symbol,
                phenotype['Target full name'],
                chemical_structure_class,
            )
            was_found, key = self.check_exists('chemical_species', record, cursor)
            if not was_found:
                cursor.execute(
                    self.generate_basic_insert_query('chemical_species'),
                    record,
                )
                chemical_species_identifiers_by_symbol[symbol] = str(
                    identifier)
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
        for _, phenotype in channels.iterrows():
            symbol = phenotype['Name']
            record = (
                str(identifier),
                str(chemical_species_identifiers_by_symbol[symbol]),
                phenotype['Antibody'],
                phenotype['Marking mechanism'],
                measurement_study,
            )
            was_found, key = self.check_exists('biological_marking_system', record, cursor)
            if not was_found:
                cursor.execute(self.generate_basic_insert_query('biological_marking_system'),record)
                identifier = identifier + 1
            else:
                logger.debug(
                    '"biological_marking_system" %s already exists.',
                    str([''] + list(record[1:])),
                )
        logger.info('Saved %s biological marking system records.', identifier - initial_value)

        mechanism = infer_common_marking_mechanism(channels)
        cursor.execute('UPDATE specimen_measurement_study SET assay=%s WHERE name=%s ;',
                       (mechanism, measurement_study))

        cursor.execute(
            self.generate_basic_insert_query('data_analysis_study'), (data_analysis_study, ))

        identifier = self.get_next_integer_identifier('cell_phenotype', cursor)
        initial_value = identifier
        cell_phenotype_identifiers_by_symbol = {}
        number_criterion_records = 0
        for _, phenotype in phenotypes.iterrows():
            symbol = phenotype['Name']
            record = (str(identifier), symbol, symbol)
            was_found, key = self.check_exists('cell_phenotype', record, cursor)
            if not was_found:
                cursor.execute(
                    self.generate_basic_insert_query('cell_phenotype'),
                    record,
                )
                cell_phenotype_identifiers_by_symbol[symbol] = str(identifier)
                identifier = identifier + 1
                logger.debug('Recognized phenotype: %s', symbol)
            else:
                cell_phenotype_identifiers_by_symbol[symbol] = key
                logger.debug(
                    '"cell_phenotype" %s already exists.',
                    str([''] + list(record[1:])),
                )
            positive_markers = set(
                str(phenotype['Positive markers']).split(';')).difference([''])
            negative_markers = set(
                str(phenotype['Negative markers']).split(';')).difference([''])
            missing = positive_markers.union(negative_markers).difference(
                chemical_species_identifiers_by_symbol.keys()
            )
            if len(missing) > 0:
                logger.warning(
                    'Markers %s are part of phenotype %s but do not represent '
                    'any known "chemical_species". This marker is skipped.',
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
                was_found, _ = self.check_exists('cell_phenotype_criterion',
                                                 record, cursor, no_primary=True)
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
        logger.info('Saved %s cell phenotype records.',
                    identifier - initial_value)
        logger.info('Saved %s cell phenotype criterion records.',
                    number_criterion_records)

        logger.info(
            'Parsed records implied by "%s" and "%s".',
            channels_file,
            phenotypes_file,
        )
        connection.commit()
        cursor.close()
        return chemical_species_identifiers_by_symbol
