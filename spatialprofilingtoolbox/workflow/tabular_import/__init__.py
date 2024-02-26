"""The main data import workflow."""

from spatialprofilingtoolbox.workflow.common.workflow_module_exporting import WorkflowModules
from spatialprofilingtoolbox.workflow.tabular_import.job_generator import TabularImportJobGenerator
from spatialprofilingtoolbox.workflow.tabular_import.initializer import TabularImportInitializer
from spatialprofilingtoolbox.workflow.tabular_import.core import TabularImportCoreJob
from spatialprofilingtoolbox.workflow.tabular_import.integrator import TabularImportIntegrator


def check_input_parameters(params: dict[str, str | bool]) -> None:
    """Check that the input parameters are valid."""
    if 'input_path' not in params:
        raise ValueError('Must specify input_path')


components = WorkflowModules(
    is_database_visitor=False,
    assets_needed=[('tabular_import', 'main.nf', True)],
    generator=TabularImportJobGenerator,
    initializer=TabularImportInitializer,
    core_job=TabularImportCoreJob,
    integrator=TabularImportIntegrator,
    config_section_required=True,
    process_inputs=check_input_parameters,
)
