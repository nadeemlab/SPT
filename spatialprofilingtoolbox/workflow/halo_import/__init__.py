"""The main data import workflow."""
from spatialprofilingtoolbox.workflow.defaults.workflow_module_exporting import WorkflowModules

from spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.\
    halo_cell_metadata_design import HALOCellMetadataDesign

from spatialprofilingtoolbox.workflow.halo_import.job_generator import JobGenerator
from spatialprofilingtoolbox.workflow.halo_import.initializer import HALOImportInitializer
from spatialprofilingtoolbox.workflow.halo_import.computational_design import HALOImportDesign
from spatialprofilingtoolbox.workflow.halo_import.core import HALOImportCoreJob
from spatialprofilingtoolbox.workflow.halo_import.integrator import HALOImportIntegrator

components = WorkflowModules(
    generator=JobGenerator,
    initializer=HALOImportInitializer,
    dataset_design=HALOCellMetadataDesign,
    computational_design=HALOImportDesign,
    core_job=HALOImportCoreJob,
    integrator=HALOImportIntegrator,
)
