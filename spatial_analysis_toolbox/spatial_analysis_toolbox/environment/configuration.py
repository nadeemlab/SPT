
from ..dataset_designs.multiplexed_immunofluorescence.design import HALOCellMetadataDesign
from ..computation_modules.diffusion.job_generator import DiffusionJobGenerator
from ..computation_modules.diffusion.analyzer import DiffusionAnalyzer
from ..computation_modules.diffusion.integrator import DiffusionAnalysisIntegrator
from ..computation_modules.phenotype_proximity.job_generator import PhenotypeProximityJobGenerator
from ..computation_modules.phenotype_proximity.analyzer import PhenotypeProximityAnalyzer
from ..computation_modules.phenotype_proximity.integrator import PhenotypeProximityAnalysisIntegrator

config_filename = '.sat_pipeline.config'


class WorkflowModules:
    def __init__(self, generator=None, design=None, analyzer=None, integrator=None):
        self.generator = generator
        self.design = design
        self.analyzer = analyzer
        self.integrator = integrator

workflows = {
    'Multiplexed IF diffusion' : WorkflowModules(
        generator = DiffusionJobGenerator,
        design = HALOCellMetadataDesign,
        analyzer = DiffusionAnalyzer,
        integrator = DiffusionAnalysisIntegrator,
    ),
    'Multiplexed IF phenotype proximity' : WorkflowModules(
        generator = PhenotypeProximityJobGenerator,
        design = HALOCellMetadataDesign,
        analyzer = PhenotypeProximityAnalyzer,
        integrator = PhenotypeProximityAnalysisIntegrator,
    ),
}
