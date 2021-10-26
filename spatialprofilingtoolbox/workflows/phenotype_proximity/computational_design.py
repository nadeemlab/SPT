"""
The module describing the design of the phenotype proximity workflow, including
any workflow-specific metadata.
"""
import pandas as pd

from ...environment.computational_design import ComputationalDesign


class PhenotypeProximityDesign(ComputationalDesign):
    """
    The design object.
    """
    def __init__(self,
        balanced: bool=False,
        use_intensities: bool=False,
        **kwargs,
    ):
        """
        :param balanced: Whether to use balanced or unbalanced treatment of phenotype
            pairs.
        :type balanced: bool

        :param use_intensities: Whether to use continue intensity values.
        :type use_intensities: bool
        """
        super(PhenotypeProximityDesign, self).__init__(**kwargs)
        self.balanced = balanced
        self.use_intensities = use_intensities

    @staticmethod
    def get_cell_pair_counts_table_name():
        return 'phenotype_proximity_metrics'

    @staticmethod
    def get_cell_pair_counts_table_header():
        """
        :return: A list of 2-tuples, each of which is a column name followed by
            SQL-style datatype name, describing the schema for the cell pair counts
            intermediate data table.
        :rtype: list of 2-tuples
        """
        return [
            ('sample_identifier', 'TEXT'),
            ('input_filename', 'TEXT'),
            ('outcome_assignment', 'TEXT'),
            ('source_phenotype', 'TEXT'),
            ('target_phenotype', 'TEXT'),
            ('compartment', 'TEXT'),
            ('distance_limit_in_pixels', 'INTEGER'),
            ('phenotype_proximity_metric', 'NUMERIC'),
            ('source_phenotype_count', 'INTEGER'),
        ]

    def get_all_phenotype_signatures(self, by_name=False):
        """
        :param by_name: Whether to return a list (default) or a dictionary whose keys
            are the munged names. (Default False).
        :type by_name: bool

        :return: ``signature``. Signatures for all the composite phenotypes described by
            the ``complex_phenotypes_file`` table. Each signature is a dictionary with
            keys the elementary phenotypes and values either "+" or "-".
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
        signatures = elementary_signatures + complex_signatures
        if by_name:
            return {
                self.dataset_design.munge_name(signature) : signature for signature in signatures
            }
        return signatures

    def get_all_phenotype_names(self):
        """
        :return: All (composite) phenotype names.
        :rtype: list
        """
        return sorted(list(self.get_all_phenotype_signatures(by_name=True).keys()))

    @staticmethod
    def get_primary_output_feature_name(style='readable'):
        """
        :return: The name of the main numerical feature produced by the jobs.
        :rtype: str
        """
        if style == 'readable':
            return 'phenotype proximity metric'
        if style == 'sql':
            return 'phenotype_proximity_metric'

    @staticmethod
    def get_aggregated_metric_name(style='readable'):
        if style == 'readable':
            return 'aggregated metric'
        if style == 'sql':
            return 'aggregated_metric'

    def get_metric_description(self):
        if self.balanced:
            return 'cell pair counts per unit slide area'
        else:
            return 'number of neighbor cells of target type, averaged over cells of source type'

