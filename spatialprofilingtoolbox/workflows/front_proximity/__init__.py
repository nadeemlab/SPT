"""
The core of this module takes as input a collections of points, divided into two
regional classes, and calculates the distances to the front or boundary between
the classes from each cell. The results are stratified by cell phenotype and
region membership.
"""
from ..defaults.workflow_module_exporting import WorkflowModules

from ...dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign

from .job_generator import FrontProximityJobGenerator
from .core import FrontProximityCoreJob
from .computational_design import FrontProximityDesign
from .integrator import FrontProximityAnalysisIntegrator

name = 'front proximity'
components = {
    name : WorkflowModules(
        generator = FrontProximityJobGenerator,
        dataset_design = HALOCellMetadataDesign,
        computational_design = FrontProximityDesign,
        core_job = FrontProximityCoreJob,
        integrator = FrontProximityAnalysisIntegrator,
    ),
}
