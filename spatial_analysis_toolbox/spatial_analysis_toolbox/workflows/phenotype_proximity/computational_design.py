
import pandas as pd

from ...environment.computational_design import ComputationalDesign


class PhenotypeProximityDesign(ComputationalDesign):
    def __init__(
            self,
            dataset_design=None,
            complex_phenotypes_file: str=None,
            **kwargs,
        ):
        """
        Args:
            dataset_design:
                The design object describing the input data set.
            complex_phenotypes_file (str):
                The table of composite phenotypes to be considered.            
        """
        super(ComputationalDesign, self).__init__(**kwargs)
        self.dataset_design = dataset_design
        self.complex_phenotypes = pd.read_csv(
            complex_phenotypes_file,
            keep_default_na=False,
        )

    def get_database_uri(self):
        return 'phenotype_proximity.db'

    def get_stats_tests_file(self):
        """
        Returns:
            str:
                The filename to use when writing the statistical test results.
        """
        return 'phenotype_2_phenotype_proximity_tests.csv'

    def get_cell_pair_counts_table_header(self):
        """
        Returns:
            list:
                A list of 2-tuples, column name followed by SQL-style datatype name,
                describing the schema for the cell pair counts intermediate data table.
        """
        return [
            ('sample_identifier', 'TEXT'),
            ('outcome_assignment', 'TEXT'),
            ('source_phenotype', 'TEXT'),
            ('target_phenotype', 'TEXT'),
            ('compartment', 'TEXT'),
            ('distance_limit_in_pixels', 'INTEGER'),
            ('cell_pair_count_per_FOV', 'NUMERIC'),
        ]

    def get_all_phenotype_signatures(self):
        """
        Returns:
            list:
                The "signatures" for all the composite phenotypes described by the
                complex_phenotypes_file table. Each signature is a dictionary with
                keys the elementary phenotypes and values either "+" or "-".
        """
        elementary_signatures = [{name : '+'} for name in self.dataset_design.get_elementary_phenotype_names()]
        complex_signatures = []
        for i, row in self.complex_phenotypes.iterrows():
            positive_markers = sorted([m for m in row['Positive markers'].split(';') if m != ''])
            negative_markers = sorted([m for m in row['Negative markers'].split(';') if m != ''])
            signature = {}
            for marker in positive_markers:
                signature[marker] = '+'
            for marker in negative_markers:
                signature[marker] = '-'
            complex_signatures.append(signature)
        return elementary_signatures + complex_signatures
