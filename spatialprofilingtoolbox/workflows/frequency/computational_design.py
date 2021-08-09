"""
This is the module in which should be registered any metadata related to the
design of the cell phenotype frequency analysis workflow.
"""
import re

import pandas as pd

from ...environment.computational_design import ComputationalDesign


class FrequencyDesign(ComputationalDesign):
    """
    The design object.
    """
    def __init__(
            self,
            dataset_design=None,
            complex_phenotypes_file: str=None,
            **kwargs,
        ):
        """
        :param dataset_design: The design object describing the acceptable input data
            sets.

        :param complex_phenotypes_file: The table of composite phenotypes to be
            considered.
        :type complex_phenotypes_file: str
        """
        super().__init__(**kwargs)
        self.dataset_design = dataset_design
        if not complex_phenotypes_file is None:
            self.complex_phenotypes = pd.read_csv(
                complex_phenotypes_file,
                keep_default_na=False,
            )

    @staticmethod
    def get_database_uri():
        return 'frequency.db'

    @staticmethod
    def get_stats_tests_file():
        """
        :return: The filename to use when writing the statistical test results.
        :rtype: str
        """
        return 'frequency_tests.csv'

    def get_cells_header(self, style='readable'):
        """
        :param style: Either "readable" or "sql". See
            :py:meth:`get_cells_header_variable_portion`.
        :type style: str

        :return: List of 2-tuples giving the schema for the cells. Each 2-tuple is a
            column name followed by a SQL datatype name.
        :rtype: list
        """
        constant_portion = FrequencyDesign.get_cells_header_constant_portion()
        variable_portion = self.get_cells_header_variable_portion(style=style)
        return constant_portion + variable_portion

    @staticmethod
    def get_cells_header_constant_portion():
        """
        :return: A list of 2-tuples, column name followed by SQL-style datatype name,
            describing part of the schema for the cells intermediate data table.
            "Constant" refers to the fact that this portion of the schema does not
            depend on the metadata files.
        :rtype: list
        """
        return [
            ('sample_identifier', 'TEXT'),
            ('fov_index', 'INTEGER'),
            ('outcome_assignment', 'TEXT'),
            ('compartment', 'TEXT'),
            ('cell_area', 'NUMERIC'),
        ]

    def get_cells_header_variable_portion(self, style='readable'):
        """
        :param style: Either "readable" or "sql". If "sql", the '+' and '-' characters
            are replaced with SQL-friendly '$PLUS' and '$MINUS'. Default "readable".
        :type style: str

        :return: A list of 2-tuples, column name followed by SQL-style datatype name,
            describing a part of the schema for the cells intermediate data table.
            "Variable" refers to the fact that this portion depends on the complex
            phenotypes metadata.
        :rtype: list
        """
        signatures = self.get_all_phenotype_signatures()
        phenotype_names = [self.dataset_design.munge_name(signature) for signature in signatures]
        if style == 'sql':
            phenotype_names = [re.sub(r'\+', r'$PLUS', name) for name in phenotype_names]
            phenotype_names = [re.sub('-', r'$MINUS', name) for name in phenotype_names]
        phenotype_membership_columns = sorted([name + ' membership' for name in phenotype_names])
        if style == 'sql':
            phenotype_membership_columns = [
                re.sub(' ', r'$SPACE', name) for name in phenotype_membership_columns
            ]
        return [
            (column_name, 'INTEGER') for column_name in phenotype_membership_columns
        ]

    @staticmethod
    def get_fov_lookup_header():
        """
        :return: A list of 2-tuples, column name followed by SQL-style datatype name,
            describing the schema for the FOV lookup intermediate data table.
        :rtype: list
        """
        return [
            ('sample_identifier', 'TEXT'),
            ('fov_index', 'INTEGER'),
            ('fov_string', 'TEXT'),
        ]

    def get_all_phenotype_signatures(self):
        """
        :return: The "signatures" for all the composite phenotypes described by the
            ``complex_phenotypes_file`` table. Each signature is a dictionary with keys
            the elementary phenotype names and values either "+" or "-".
        :rtype: list
        """
        elementary_signatures = [
            {name : '+'} for name in self.dataset_design.get_elementary_phenotype_names()
        ]
        complex_signatures = []
        for _, row in self.complex_phenotypes.iterrows():
            positive_markers = sorted([m for m in row['Positive markers'].split(';') if m != ''])
            negative_markers = sorted([m for m in row['Negative markers'].split(';') if m != ''])
            signature = {}
            for marker in positive_markers:
                signature[marker] = '+'
            for marker in negative_markers:
                signature[marker] = '-'
            complex_signatures.append(signature)
        return elementary_signatures + complex_signatures
