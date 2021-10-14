"""
The core of this module takes as input a collections of points, divided into two
regional classes, and calculates the distances to the front or boundary between
the classes from each cell. The results are stratified by cell phenotype and
region membership.
"""
from ...environment.workflow_modules import WorkflowModules

from ...dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign

from .job_generator import FrontProximityJobGenerator
from .analyzer import FrontProximityAnalyzer
from .computational_design import FrontProximityDesign
from .integrator import FrontProximityAnalysisIntegrator

components = {
    'Multiplexed IF front proximity' : WorkflowModules(
        generator = FrontProximityJobGenerator,
        dataset_design = HALOCellMetadataDesign,
        computational_design = FrontProximityDesign,
        analyzer = FrontProximityAnalyzer,
        integrator = FrontProximityAnalysisIntegrator,
    ),
}
