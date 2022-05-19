
import pandas as pd

from ...environment.logging.log_formats import colorized_logger

logger = colorized_logger(__name__)


class Integrator:
    def __init__(
        self,
        computational_design=None,
        stats_tests_file:str = None,
        feature_matrix_filename: str=None,
        **kwargs,
    ):
        self.computational_design = computational_design
        self.stats_tests_file = stats_tests_file
        self.feature_matrix_filename = feature_matrix_filename

    def calculate(self):
        self._calculate()
        tables = self.get_tall_feature_tables()
        if not tables is None:
            feature_matrix = Integrator.generate_wide_feature_matrix(*tables)
            feature_matrix.to_csv(self.feature_matrix_filename, index=False, sep='\t')

    def _calculate(self):
        """
        To be overwritten by implementations.
        """
        self.write_placeholder_stats()

    def write_placeholder_stats(self):
        logger.info('Stats calculation not implemented')
        with open(self.stats_tests_file, 'wt') as file:
            file.write('')

    def get_tall_feature_tables(self):
        logger.warning('Writing out sample-level features not implemented.')
        return None

    @staticmethod
    def generate_wide_feature_matrix(
        feature_specifier,
        feature_specification,
        quantitative_feature_value,
    ):
        specification_tuples = {
            specification : tuple(specifiers.sort_values(by='ordinality')['specifier'])
            for specification, specifiers in feature_specifier.groupby('feature_specification')
        }
        specification_names = {
            specification : Integrator.specification_tuple_to_string(t)
            for specification, t in specification_tuples.items()
        }
        records = []
        for subject, feature_values in quantitative_feature_value.groupby('subject'):
            record = {
                specification_names[row['feature']] : row['value']
                for i, row in feature_values.iterrows()
            }
            record['subject'] = subject
            records.append(record)
        feature_matrix = pd.DataFrame(records).sort_values(by='subject')
        sorted_columns = sorted(feature_matrix.columns)
        sorted_columns.remove('subject')
        sorted_columns = ['subject'] + sorted_columns
        return feature_matrix[sorted_columns]

    @staticmethod
    def specification_tuple_to_string(
        specification,
        string_format = 'readable',
    ):
        if string_format == 'readable':
            return ' '.join(specification)
        if string_format == 'escaped':
            return '_'.join(specification)
        if string_format == 'tuple':
            return '(' + '", "'.join(specification) + ')'
        logger.error('String format %s not supported.', string_format)

