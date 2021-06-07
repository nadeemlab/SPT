
from ...environment.computational_design import ComputationalDesign


class PhenotypeProximityDesign(ComputationalDesign):
    def __init__(self, **kwargs):
        super(ComputationalDesign, self).__init__(**kwargs)

    def get_database_uri(self):
        return 'phenotype_proximity.db'

    def get_stats_tests_file(self):
        return 'phenotype_2_phenotype_proximity_tests.csv'

    def get_cell_pair_counts_table_header(self):
        return [
            ('sample_identifier', 'TEXT'),
            ('outcome_assignment', 'TEXT'),
            ('source_phenotype', 'TEXT'),
            ('target_phenotype', 'TEXT'),
            ('compartment', 'TEXT'),
            ('distance_limit_in_pixels', 'INTEGER'),
            ('cell_pair_count_per_FOV', 'NUMERIC'),
        ]
