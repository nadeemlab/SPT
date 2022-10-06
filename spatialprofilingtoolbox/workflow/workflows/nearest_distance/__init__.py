"""
This module computes basic density statistics for each phenotype, without
regard to spatial information.
"""
from ..defaults.workflow_module_exporting import WorkflowModules

from ...dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign

from ..defaults.job_generator import JobGenerator
from .initializer import NearestDistanceInitializer
from .core import NearestDistanceCoreJob
from .computational_design import NearestDistanceDesign
from .integrator import NearestDistanceAnalysisIntegrator

name = 'nearest distance to compartment'
components = WorkflowModules(
    generator = JobGenerator,
    initializer = NearestDistanceInitializer,
    dataset_design = HALOCellMetadataDesign,
    computational_design = NearestDistanceDesign,
    core_job = NearestDistanceCoreJob,
    integrator = NearestDistanceAnalysisIntegrator,
)
