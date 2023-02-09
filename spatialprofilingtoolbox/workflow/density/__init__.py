"""
This module computes basic density statistics for each phenotype, without
regard to spatial information.
"""
from spatialprofilingtoolbox.workflow.defaults.workflow_module_exporting import WorkflowModules
from spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.halo_cell_metadata_design\
    import HALOCellMetadataDesign
from spatialprofilingtoolbox.workflow.halo_import.job_generator import JobGenerator
from spatialprofilingtoolbox.workflow.density.initializer import DensityInitializer
from spatialprofilingtoolbox.workflow.density.core import DensityCoreJob
from spatialprofilingtoolbox.workflow.density.computational_design import DensityDesign
from spatialprofilingtoolbox.workflow.density.integrator import DensityAnalysisIntegrator

components = WorkflowModules(
    generator=JobGenerator,
    initializer=DensityInitializer,
    dataset_design=HALOCellMetadataDesign,
    computational_design=DensityDesign,
    core_job=DensityCoreJob,
    integrator=DensityAnalysisIntegrator,
)
