"""
The module describing the design of the phenotype proximity workflow, including
any workflow-specific metadata.
"""
from spatialprofilingtoolbox.workflow.defaults.computational_design import ComputationalDesign


class PhenotypeProximityDesign(ComputationalDesign):
    """
    The design object.
    """

    def __init__(self,
                 balanced: bool = False,
                 use_intensities: bool = False,
                 **kwargs,
                 ):
        """
        :param balanced: Whether to use balanced or unbalanced treatment of phenotype
            pairs.
        :type balanced: bool

        :param use_intensities: Whether to use continue intensity values.
        :type use_intensities: bool
        """
        super().__init__(**kwargs)
        self.balanced = balanced
        self.use_intensities = use_intensities

    @staticmethod
    def solicit_cli_arguments(parser):
        parser.add_argument(
            '--use-intensities',
            dest='use_intensities',
            action='store_true',
        )
        parser.add_argument(
            '--balanced',
            dest='balanced',
            action='store_true',
        )

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

    def get_all_phenotype_signatures_by_name(self):
        """
        Returns a dictionary whose keys are the "munged" names, and values are
        the phenotype signatures. See get_all_phenotype_signatures for details
        regarging the values.
        """
        signatures = self.get_all_phenotype_signatures()
        return {
            self.dataset_design.munge_name(signature): signature for signature in signatures
        }

    def get_all_phenotype_names(self):
        """
        :return: All (composite) phenotype names.
        :rtype: list
        """
        return sorted(list(self.get_all_phenotype_signatures_by_name().keys()))

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
        return ''

    @staticmethod
    def get_aggregated_metric_name(style='readable'):
        if style == 'readable':
            return 'aggregated metric'
        if style == 'sql':
            return 'aggregated_metric'
        return ''

    def get_metric_description(self):
        if self.balanced:
            return 'cell pair counts per unit slide area'
        return 'number of neighbor cells of target type, averaged over cells of source type'

    @staticmethod
    def uses_database():
        return True

    def get_workflow_specific_columns(self, style):
        pass
