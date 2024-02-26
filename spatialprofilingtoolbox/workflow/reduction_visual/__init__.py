"""
The core of this module takes as input two collections of points, and calculates
the density with which a pair of points from the respective collections occur
near each other, per unit cell area. In an unbalanced mode, it calculates, for
cells of a given phenotype, the average number of neighbors of another given
phenotype.

Taken as a whole the phenotype proximity analysis pipeline provides statistical
test results and figures that assess the efficacy of proximity-related metrics
as discriminators of selected correlates.
"""

from spatialprofilingtoolbox.workflow.common.workflow_module_exporting import WorkflowModules
from spatialprofilingtoolbox.workflow.reduction_visual.job_generator import \
    ReductionVisualJobGenerator
from spatialprofilingtoolbox.workflow.reduction_visual.initializer import ReductionVisualInitializer
from spatialprofilingtoolbox.workflow.reduction_visual.core import ReductionVisualCoreJob
from spatialprofilingtoolbox.workflow.reduction_visual.integrator import \
    ReductionVisualAnalysisIntegrator

components = WorkflowModules(
    is_database_visitor=True,
    assets_needed=[('assets', 'main_visitor.nf', True)],
    generator=ReductionVisualJobGenerator,
    initializer=ReductionVisualInitializer,
    core_job=ReductionVisualCoreJob,
    integrator=ReductionVisualAnalysisIntegrator,
)
