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
from ...environment.workflow_modules import WorkflowModules

from ...dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign

from .job_generator import PhenotypeProximityJobGenerator
from .analyzer import PhenotypeProximityAnalyzer
from .computational_design import PhenotypeProximityDesign
from .integrator import PhenotypeProximityAnalysisIntegrator

components = {
    'Multiplexed IF phenotype proximity' : WorkflowModules(
        generator = PhenotypeProximityJobGenerator,
        dataset_design = HALOCellMetadataDesign,
        computational_design = PhenotypeProximityDesign,
        analyzer = PhenotypeProximityAnalyzer,
        integrator = PhenotypeProximityAnalysisIntegrator,
    ),	
}
