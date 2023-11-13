"""This module generates cell graphs for a given study in a parallelizable fashion."""

from spatialprofilingtoolbox.workflow.common.workflow_module_exporting import WorkflowModules
from spatialprofilingtoolbox.workflow.graph_generation.job_generator import GraphGenerationJobGenerator
from spatialprofilingtoolbox.workflow.graph_generation.initializer import \
    GraphGenerationInitializer
from spatialprofilingtoolbox.workflow.graph_generation.core import GraphGenerationCoreJob
from spatialprofilingtoolbox.workflow.graph_generation.integrator import \
    GraphGenerationIntegrator

components = WorkflowModules(
    is_database_visitor=True,
    generator=GraphGenerationJobGenerator,
    initializer=GraphGenerationInitializer,
    core_job=GraphGenerationCoreJob,
    integrator=GraphGenerationIntegrator,
)
