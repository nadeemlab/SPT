
from ...environment.computational_design import ComputationalDesign


class DiffusionDesign(ComputationalDesign):
    def __init__(self, **kwargs):
        super(ComputationalDesign, self).__init__(**kwargs)

    def get_database_uri(self):
        return 'diffusion.db'

    def get_job_metadata_header(self):
        return [
            'Input file identifier',
            'Sample ID',
            'Job status',
            'Regional compartment',
            'job_activity_id',
            'distance_type',
        ]

    def get_probabilities_table_header(self):
        return [
            'transition_probability',
            'distance_type',
            'job_activity_id',
            'temporal_offset',
            'marker',
        ]
