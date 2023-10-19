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

from spatialprofilingtoolbox.workflow.tabular_import.job_generator import JobGenerator
from spatialprofilingtoolbox.workflow.phenotype_proximity.job_generator import ProximityJobGenerator
from spatialprofilingtoolbox.workflow.phenotype_proximity.initializer import \
    PhenotypeProximityInitializer
from spatialprofilingtoolbox.workflow.phenotype_proximity.core import PhenotypeProximityCoreJob
from spatialprofilingtoolbox.workflow.phenotype_proximity.integrator import \
    PhenotypeProximityAnalysisIntegrator

components = WorkflowModules(
    is_database_visitor=True,
    generator=ProximityJobGenerator,
    initializer=PhenotypeProximityInitializer,
    core_job=PhenotypeProximityCoreJob,
    integrator=PhenotypeProximityAnalysisIntegrator,
)
