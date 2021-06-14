import configparser

from ..dataset_designs.multiplexed_immunofluorescence.design import HALOCellMetadataDesign
from ..computation_modules.diffusion.job_generator import DiffusionJobGenerator
from ..computation_modules.diffusion.computational_design import DiffusionDesign
from ..computation_modules.diffusion.analyzer import DiffusionAnalyzer
from ..computation_modules.diffusion.integrator import DiffusionAnalysisIntegrator
from ..computation_modules.phenotype_proximity.job_generator import PhenotypeProximityJobGenerator
from ..computation_modules.phenotype_proximity.computational_design import PhenotypeProximityDesign
from ..computation_modules.phenotype_proximity.analyzer import PhenotypeProximityAnalyzer
from ..computation_modules.phenotype_proximity.integrator import PhenotypeProximityAnalysisIntegrator

config_filename = '.sat_pipeline.config'


class WorkflowModules:
    def __init__(self, generator=None, design=None, computational_design=None, analyzer=None, integrator=None):
        self.generator = generator
        self.design = design
        self.computational_design = computational_design
        self.analyzer = analyzer
        self.integrator = integrator

workflows = {
    'Multiplexed IF diffusion' : WorkflowModules(
        generator = DiffusionJobGenerator,
        dataset_design = HALOCellMetadataDesign,
        computational_design = DiffusionDesign,
        analyzer = DiffusionAnalyzer,
        integrator = DiffusionAnalysisIntegrator,
    ),
    'Multiplexed IF phenotype proximity' : WorkflowModules(
        generator = PhenotypeProximityJobGenerator,
        dataset_design = HALOCellMetadataDesign,
        computational_design = PhenotypeProximityDesign,
        analyzer = PhenotypeProximityAnalyzer,
        integrator = PhenotypeProximityAnalysisIntegrator,
    ),
}

def get_config_parameters_from_file():
    config = configparser.ConfigParser()
    config.read(config_filename)
    parameters = dict(config['default'])
    return parameters

def write_config_parameters_to_file(parameters):
    config = configparser.ConfigParser()
    config['default'] = parameters
    with open(config_filename, 'w') as file:
        config.write(file)
