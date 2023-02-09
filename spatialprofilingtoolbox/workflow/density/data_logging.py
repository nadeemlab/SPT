"""
These functions provide detailed data-specific logging for the cell phenotype
density workflow. The log messages are intended to aid in tracking data value
provenance in particular runs.
"""

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

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
        readable_names = {
            header2[i][0]: header1[i][0] for i in range(len(header1))
        }
        for item in header2:
            phenotype = item[0]
            readable = readable_names[phenotype]
            number = cells[cells[phenotype] == 1].shape[0]
            logger.debug('%s cells (header value: %s). Count is  %s.',
                         readable, phenotype, number)

    @staticmethod
    def log_cell_areas_one_fov(cells, fov_lookup_dict):
        """
        Reports the cells areas for a single FOV in a single image, by phenotype.
        """
        example_sample_identifier = list(cells['sample_identifier'])[0]
        example_fov_index = list(cells['fov_index'])[0]
        example_fov_string = fov_lookup_dict[(
            example_sample_identifier, example_fov_index)]
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
        logger.debug('(Table has %s rows, above is truncated at %s)',
                     sample_focused_cells.shape[0], truncation)

    @staticmethod
    def log_test_input(row, df1, df2):
        """
        Reports information about the input to one instance of a statistical test.
        """
        phenotype_name = row['phenotype']
        phenotype_column = phenotype_name + ' normalized cell area sum'
        logger.debug('Logging details in one statistical test case.')
        logger.debug('Outcome pair: %s, %s',
                     row['outcome 1'], row['outcome 2'])
        logger.debug('Phenotype: %s', row['phenotype'])
        dict1 = {row['sample_identifier']: row[phenotype_column]
                 for i, row in df1.iterrows()}
        logger.debug(
            'Cell areas summed over FOVs and normalized (1): %s', dict1)
        dict2 = {row['sample_identifier']: row[phenotype_column]
                 for i, row in df2.iterrows()}
        logger.debug(
            'Cell areas summed over FOVs and normalized (2): %s', dict2)
        logger.debug('Number of values 1: %s', len(dict1))
        logger.debug('Number of values 2: %s', len(dict2))
