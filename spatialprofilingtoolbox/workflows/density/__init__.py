"""
This module computes basic density statistics for each phenotype, without
regard to spatial information.
"""
from ...environment.workflow_modules import WorkflowModules

from ...dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign

from .job_generator import DensityJobGenerator
from .analyzer import DensityAnalyzer
from .computational_design import DensityDesign
from .integrator import DensityAnalysisIntegrator

components =  {
    'Multiplexed IF density' : WorkflowModules(
        generator = DensityJobGenerator,
        dataset_design = HALOCellMetadataDesign,
        computational_design = DensityDesign,
        analyzer = DensityAnalyzer,
        integrator = DensityAnalysisIntegrator,
    ),
}
