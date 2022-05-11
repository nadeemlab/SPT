"""
This module computes basic density statistics for each phenotype, without
regard to spatial information.
"""
from ..defaults.workflow_module_exporting import WorkflowModules

from ...dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign

from .job_generator import DensityJobGenerator
from .core import DensityCoreJob
from .computational_design import DensityDesign
from .integrator import DensityAnalysisIntegrator

name = 'phenotype density'
components =  {
    name : WorkflowModules(
        generator = DensityJobGenerator,
        dataset_design = HALOCellMetadataDesign,
        computational_design = DensityDesign,
        core_job = DensityCoreJob,
        integrator = DensityAnalysisIntegrator,
    ),
}
