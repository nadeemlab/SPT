"""
These functions provide detailed data-specific logging for the cell phenotype
density workflow. The log messages are intended to aid in tracking data value
provenance in particular runs.
"""

from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class DensityDataLogger:
    """
    Convenience class.
    """
    @staticmethod
    def log_number_by_type(computational_design, cells, style='sql'):
        header1 = computational_design.get_cells_header_variable_portion(
            style='readable',
        )
        if style == 'readable':
            header2 = header1
        else:
            header2 = computational_design.get_cells_header_variable_portion(
                style='sql',
            )
        readable_names =  {
            header2[i][0] : header1[i][0] for i in range(len(header1))
        }
        for item in header2:
            pheno = item[0]
            readable = readable_names[pheno]
            number = cells[cells[pheno] == 1].shape[0]
            logger.debug('%s cells (header value: %s). Count is  %s.', readable, pheno, number)

    @staticmethod
    def log_cell_areas_one_fov(cells, fov_lookup_dict):
        """
        Reports the cells areas for a single FOV in a single image, by phenotype.
        """
        example_sample_identifier = list(cells['sample_identifier'])[0]
        example_fov_index = list(cells['fov_index'])[0]
        example_fov_string = fov_lookup_dict[(example_sample_identifier, example_fov_index)]
        condition = (
            (cells['sample_identifier'] == example_sample_identifier) &
            (cells['fov_index'] == example_fov_index)
        )
        logger.debug(
            'Logging cells areas in sample %s FOV %s, i.e. "%s".',
            example_sample_identifier,
            example_fov_index,
            example_fov_string,
        )
        sample_focused_cells = cells[condition].sort_values(by='cell_area')
        truncation = 100
        head = sample_focused_cells.head(truncation)
        logger.debug(
            '(Transposed for readability:)\n%s',
            head.transpose().to_string(),
        )
        logger.debug('(Table has %s rows, above is truncated at %s)', sample_focused_cells.shape[0], truncation)

    @staticmethod
    def log_normalization_factors(areas_all_phenotypes_dict):
        """
        Reports the summed cell areas over all phenotypes and FOVs in a given
        compartment, one value for each sample and compartment type.
        """
        logger.debug(
            'Compartmental areas, total over all phenotypes and FOVs (sample fixed):\n%s',
            '\n'.join([
                ''.join([
                    'Sample ID: ',
                    key[0],
                    ', ',
                    'Compartment: ',
                    key[1],
                    ', ',
                    'Cell area: ',
                    str(value),
                ]) for key, value in areas_all_phenotypes_dict.items()
            ]),
        )

    @staticmethod
    def log_normalized_areas(cells, area_sums, normalized_sum_columns):
        """
        Reports the cell areas after normalization.
        """
        example_phenotype = list(normalized_sum_columns.values())[0]
        example_compartment = list(cells['compartment'])[0]
        logger.debug(
            'Logging "%s", in %s.',
            example_phenotype,
            example_compartment,
        )
        example_areas = [
            (r['sample_identifier'], r['compartment'], r[example_phenotype])
            for i, r in area_sums.iterrows() if r['compartment'] == example_compartment
        ]
        string_rep = '\n'.join([' '.join([str(elt) for elt in row]) for row in example_areas])
        logger.debug('Normalized cell area fractions:\n%s', string_rep)

    @staticmethod
    def log_test_input(row, df1, df2):
        """
        Reports information about the input to one instance of a statistical test.
        """
        phenotype_name = row['phenotype']
        phenotype_column = phenotype_name + ' normalized cell area sum'
        logger.debug('Logging details in one statistical test case.')
        logger.debug('Outcome pair: %s, %s', row['outcome 1'], row['outcome 2'])
        logger.debug('Compartment: %s', row['compartment'])
        logger.debug('Phenotype: %s', row['phenotype'])
        dict1 = {row['sample_identifier'] : row[phenotype_column] for i, row in df1.iterrows()}
        logger.debug('Cell areas summed over FOVs and normalized (1): %s', dict1)
        dict2 = {row['sample_identifier'] : row[phenotype_column] for i, row in df2.iterrows()}
        logger.debug('Cell areas summed over FOVs and normalized (2): %s', dict2)
        logger.debug('Number of values 1: %s', len(dict1))
        logger.debug('Number of values 2: %s', len(dict2))
