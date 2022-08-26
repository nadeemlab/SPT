
from ..defaults.workflow_module_exporting import WorkflowModules

from ...dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign

from ..defaults.job_generator import JobGenerator
from .initializer import HALOImportInitializer
from .computational_design import HALOImportDesign
from .core import HALOImportCoreJob
from .integrator import HALOImportIntegrator

components = WorkflowModules(
    generator = JobGenerator,
    initializer = HALOImportInitializer,
    dataset_design = HALOCellMetadataDesign,
    computational_design = HALOImportDesign,
    core_job = HALOImportCoreJob,
    integrator = HALOImportIntegrator,
)
