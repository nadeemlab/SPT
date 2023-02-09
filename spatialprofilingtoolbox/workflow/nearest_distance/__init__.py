"""
This module computes basic density statistics for each phenotype, without
regard to spatial information.
"""
from spatialprofilingtoolbox.workflow.common.workflow_module_exporting import WorkflowModules

from \
    spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.halo_cell_metadata_design \
    import HALOCellMetadataDesign

from spatialprofilingtoolbox.workflow.halo_import.job_generator import JobGenerator
from spatialprofilingtoolbox.workflow.nearest_distance.initializer import NearestDistanceInitializer
from spatialprofilingtoolbox.workflow.nearest_distance.core import NearestDistanceCoreJob
from spatialprofilingtoolbox.workflow.nearest_distance.computational_design import \
    NearestDistanceDesign
from spatialprofilingtoolbox.workflow.nearest_distance.integrator import \
    NearestDistanceAnalysisIntegrator

NAME = 'nearest distance to compartment'
components = WorkflowModules(
    generator=JobGenerator,
    initializer=NearestDistanceInitializer,
    dataset_design=HALOCellMetadataDesign,
    computational_design=NearestDistanceDesign,
    core_job=NearestDistanceCoreJob,
    integrator=NearestDistanceAnalysisIntegrator,
)
