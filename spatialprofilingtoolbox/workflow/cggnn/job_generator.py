"""Generate a list of parallelizable jobs for the CG GNN pipeline."""

from pandas import DataFrame

from spatialprofilingtoolbox.workflow.component_interfaces.job_generator import JobGenerator
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CGGNNJobGenerator(JobGenerator):
    """Generate a list of parallelizable jobs for the CG GNN pipeline.

    Broadly speaking, this job isn't parallelizable, although the training phase should use multiple
    cores (but just one GPU).
    """

    def __init__(self) -> None:
        pass

    def write_job_specification_table(self, job_specification_table_filename: str) -> None:
        DataFrame([{
            'job_index': 0,
        }]).to_csv(job_specification_table_filename, index=False, header=True)
