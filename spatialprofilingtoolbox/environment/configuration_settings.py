import importlib.resources

from ..workflows.diffusion import components as diffusion_workflow
from ..workflows.phenotype_proximity import components as phenotype_proximity_workflow
from ..workflows.front_proximity import components as front_proximity_workflow
from ..workflows.density import components as density_workflow

workflows = {
    **diffusion_workflow,
    **phenotype_proximity_workflow,
    **front_proximity_workflow,
    **density_workflow,
}

config_filename = '.spt_pipeline.json'

def get_version():
    with importlib.resources.path('spatialprofilingtoolbox', 'version.txt') as path:
        with open(path, 'r') as file:
            version = file.read().rstrip('\n')
    return version
