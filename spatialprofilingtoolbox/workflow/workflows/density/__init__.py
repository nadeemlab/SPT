"""
This module computes basic density statistics for each phenotype, without
regard to spatial information.
"""
from ..defaults.workflow_module_exporting import WorkflowModules

from ...dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign

from ..defaults.job_generator import JobGenerator
from .initializer import DensityInitializer
from .core import DensityCoreJob
from .computational_design import DensityDesign
from .integrator import DensityAnalysisIntegrator

components = WorkflowModules(
    generator = JobGenerator,
    initializer = DensityInitializer,
    dataset_design = HALOCellMetadataDesign,
    computational_design = DensityDesign,
    core_job = DensityCoreJob,
    integrator = DensityAnalysisIntegrator,
)
