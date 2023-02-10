"""The main data import workflow."""

from spatialprofilingtoolbox.workflow.common.workflow_module_exporting import WorkflowModules
from spatialprofilingtoolbox.workflow.tabular_import.job_generator import TabularImportJobGenerator
from spatialprofilingtoolbox.workflow.tabular_import.initializer import TabularImportInitializer
from spatialprofilingtoolbox.workflow.tabular_import.core import TabularImportCoreJob
from spatialprofilingtoolbox.workflow.tabular_import.integrator import TabularImportIntegrator

components = WorkflowModules(
    is_database_visitor=False,
    generator=TabularImportJobGenerator,
    initializer=TabularImportInitializer,
    core_job=TabularImportCoreJob,
    integrator=TabularImportIntegrator,
)
