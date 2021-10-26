
import pandas as pd

from ...environment.computational_design import ComputationalDesign


class DiffusionDesign(ComputationalDesign):
    def __init__(self,
        save_graphml: bool=False,
        **kwargs,
    ):
        """
        :param save_graphml: Whether to save GraphML files as additional output.
        :type save_graphml: bool
        """
        super(DiffusionDesign, self).__init__(**kwargs)
        self.save_graphml = save_graphml

    def should_save_graphml(self):
        return self.save_graphml

    @staticmethod
    def get_regional_compartments():
        return ('tumor', 'edge', 'nontumor')

    @staticmethod
    def get_diffusion_distances_table_name():
        return 'diffusion_distances'

    @staticmethod
    def get_probabilities_table_header():
        """
        Returns:
            list:
                The schema (header / column names) for the primary output data resulting
                from the diffusion calculations.
        """
        return [
            'diffusion_distance',
            'distance_type',
            'job_identifier',
            'sample_id',
            'temporal_offset',
            'marker',
        ]

    @staticmethod
    def get_diffusion_distances_summarized_header():
        """
        Returns:
            list:
                The schema (header / column names) for the sample-level summary metrics
                of the primary output data.
        """
        return [
            ('Sample_ID', 'TEXT'),
            ('Outcome_assignment', 'TEXT'),
            ('Marker', 'TEXT'),
            ('Diffusion_kernel_distance_type', 'TEXT'),
            ('Temporal_offset', 'NUMERIC'),
            ('Mean_diffusion_distance', 'NUMERIC'),
            ('Median_diffusion_distance', 'NUMERIC'),
            ('Variance_diffusion_distance', 'NUMERIC'),
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
