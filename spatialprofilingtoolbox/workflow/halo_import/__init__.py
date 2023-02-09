"""The main data import workflow."""

from spatialprofilingtoolbox.workflow.common.workflow_module_exporting import WorkflowModules
from spatialprofilingtoolbox.workflow.halo_import.job_generator import JobGenerator
from spatialprofilingtoolbox.workflow.halo_import.initializer import HALOImportInitializer
from spatialprofilingtoolbox.workflow.halo_import.core import HALOImportCoreJob
from spatialprofilingtoolbox.workflow.halo_import.integrator import HALOImportIntegrator

components = WorkflowModules(
    is_database_visitor=False,
    generator=JobGenerator,
    initializer=HALOImportInitializer,
    core_job=HALOImportCoreJob,
    integrator=HALOImportIntegrator,
)
