"""
The core of this module takes as input a collections of points, divided into two
regional classes, and calculates the distances to the front or boundary between
the classes from each cell. The results are stratified by cell phenotype and
region membership.
"""
from spatialprofilingtoolbox.workflow.defaults.workflow_module_exporting import WorkflowModules

from spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.halo_cell_metadata_design \
    import HALOCellMetadataDesign

from spatialprofilingtoolbox.workflow.defaults.job_generator import JobGenerator
from spatialprofilingtoolbox.workflow.front_proximity.initializer import FrontProximityInitializer
from spatialprofilingtoolbox.workflow.front_proximity.core import FrontProximityCoreJob
from spatialprofilingtoolbox.workflow.front_proximity.computational_design import \
    FrontProximityDesign
from spatialprofilingtoolbox.workflow.front_proximity.integrator import \
    FrontProximityAnalysisIntegrator

components = WorkflowModules(
    generator=JobGenerator,
    initializer=FrontProximityInitializer,
    dataset_design=HALOCellMetadataDesign,
    computational_design=FrontProximityDesign,
    core_job=FrontProximityCoreJob,
    integrator=FrontProximityAnalysisIntegrator,
)