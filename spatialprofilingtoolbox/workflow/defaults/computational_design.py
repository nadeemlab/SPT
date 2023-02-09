"""
Interface for a class meant to describe the design of the overall workflow,
for a given workflow.
"""
# import re

# import pandas as pd

# from spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.halo_cell_metadata_design\
#     import HALOCellMetadataDesign
# from spatialprofilingtoolbox.workflow.defaults.cli_arguments import add_argument
# from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

# logger = colorized_logger(__name__)


# class ComputationalDesign:
#     """
#     Subclass this object to collect together any metadata that is specific to a
#     particular pipeline/workflow's computation stage.
#     """

#     def __init__(self,
#                  dataset_design: HALOCellMetadataDesign,
#                  metrics_database_filename: str = 'metrics_default.db',
#                  dichotomize: bool = False,
#                  composite_phenotypes_file: str = '',
#                  **kwargs,  # pylint: disable=unused-argument
#                  ):
#         """
#         :param dataset_design: The design object describing the input data set.

#         :param metrics_database_filename: Name for sqlite database.
#         :type metrics_database_filename: str

#         :param dichotomize: Default False. Whether to do auto-thresholding to
#             dichotomize the continuous input variables.
#         :type dichotomize: bool
#         """
#         self.dataset_design = dataset_design
#         self.metrics_database_filename = metrics_database_filename
#         self.complex_phenotypes = pd.read_csv(
#             composite_phenotypes_file,
#             keep_default_na=False,
#         )
#         self.dichotomize = dichotomize

#     @staticmethod
#     def solicit_cli_arguments(parser):
#         add_argument(parser, 'metrics database')
#         add_argument(parser, 'phenotypes file')
#         add_argument(parser, 'dichotomize')

#     def get_database_uri(self):
#         return self.metrics_database_filename

#     def get_performance_report_filename(self):
#         return self.metrics_database_filename.rstrip('.db') + '.csv'

#     @staticmethod
#     def uses_database():
#         return False

#     @staticmethod
#     def is_database_visitor():
#         return False

#     def get_all_phenotype_signatures(self):
#         """
#         :return: The "signatures" for all the composite phenotypes described by the
#             ``complex_phenotypes_file`` table. Each signature is a dictionary with keys
#             the elementary phenotype names and values either "+" or "-".
#         :rtype: list
#         """
#         elementary_signatures = [
#             {name: '+'} for name in self.dataset_design.get_elementary_phenotype_names()
#         ]
#         complex_signatures = []
#         for _, row in self.complex_phenotypes.iterrows():
#             positive_markers = sorted(
#                 [m for m in row['Positive markers'].split(';') if m != ''])
#             negative_markers = sorted(
#                 [m for m in row['Negative markers'].split(';') if m != ''])
#             signature = {}
#             for marker in positive_markers:
#                 signature[marker] = '+'
#             for marker in negative_markers:
#                 signature[marker] = '-'
#             complex_signatures.append(signature)
#         return elementary_signatures + complex_signatures

#     def get_phenotype_signatures_by_name(self):
#         signatures = self.get_all_phenotype_signatures()
#         return {self.dataset_design.munge_name(signature): signature for signature in signatures}

#     def get_phenotype_names(self):
#         signatures_by_name = self.get_phenotype_signatures_by_name()
#         phenotype_names = sorted(signatures_by_name.keys())
#         return phenotype_names

#     @staticmethod
#     def get_fov_lookup_header():
#         """
#         :return: A list of 2-tuples, column name followed by SQL-style datatype name,
#             describing the schema for the FOV lookup intermediate data table.
#         :rtype: list
#         """
#         return [
#             ('sample_identifier', 'TEXT'),
#             ('fov_index', 'INTEGER'),
#             ('fov_string', 'TEXT'),
#         ]

#     def get_cells_header_variable_portion(self, style='readable'):
#         """
#         :param style: Either "readable" or "sql". If "sql", the '+' and '-' characters
#             are replaced with SQL-friendly '$PLUS' and '$MINUS'. Default "readable".
#         :type style: str

#         :return: A list of 2-tuples, column name followed by SQL-style datatype name,
#             describing a part of the schema for the cells intermediate data table.
#             "Variable" refers to the fact that this portion depends on the complex
#             phenotypes metadata.
#         :rtype: list
#         """
#         signatures = self.get_all_phenotype_signatures()
#         phenotype_names = sorted([self.dataset_design.munge_name(signature) for signature
#                                   in signatures])
#         if style == 'sql':
#             phenotype_names = [re.sub(r'\+', r'$PLUS', name) for name in phenotype_names]
#             phenotype_names = [re.sub('-', r'$MINUS', name) for name in phenotype_names]
#         phenotype_membership_columns = [name + ' membership' for name in phenotype_names]
#         if style == 'sql':
#             phenotype_membership_columns = [
#                 re.sub(' ', r'$SPACE', name) for name in phenotype_membership_columns
#             ]

#         extra = self.get_workflow_specific_columns(style)

#         return [
#             (column_name, 'INTEGER') for column_name in phenotype_membership_columns
#         ] + [
#             (column_name, 'NUMERIC') for column_name in extra
#         ]

#     def get_workflow_specific_columns(self, style):
#         raise NotImplementedError()

#     def get_cells_header_constant_portion(self):
#         """
#         :return: A list of 2-tuples, column name followed by SQL-style datatype name,
#             describing part of the schema for the cells intermediate data table.
#             "Constant" refers to the fact that this portion of the schema does not
#             depend on the metadata files.
#         :rtype: list
#         """
#         return [
#             ('sample_identifier', 'TEXT'),
#             ('fov_index', 'INTEGER'),
#             ('outcome_assignment', 'TEXT'),
#             ('compartment', 'TEXT'),
#             ('cell_area', 'NUMERIC'),
#         ]

#     def get_cells_header(self, style='readable'):
#         """
#         :param style: Either "readable" or "sql". See
#             :py:meth:`get_cells_header_variable_portion`.
#         :type style: str

#         :return: List of 2-tuples giving the schema for the cells. Each 2-tuple is a
#             column name followed by a SQL datatype name.
#         :rtype: list
#         """
#         constant_portion = self.get_cells_header_constant_portion()
#         variable_portion = self.get_cells_header_variable_portion(style=style)
#         return constant_portion + variable_portion
