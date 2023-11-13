"""Generate a list of parallelizable jobs for the graph generation pipeline."""

from spatialprofilingtoolbox.workflow.component_interfaces.job_generator import JobGenerator


class GraphGenerationJobGenerator(JobGenerator):
    """Job generator for graph generation workflow."""

    def write_job_specification_table(self, job_specification_table_filename):
        pass
