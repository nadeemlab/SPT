import importlib.resources

from ..workflows.diffusion import components as diffusion_workflow
from ..workflows.phenotype_proximity import components as phenotype_proximity_workflow
from ..workflows.front_proximity import components as front_proximity_workflow
from ..workflows.density import components as density_workflow
from ..workflows.diffusion import name as diffusion_name
from ..workflows.phenotype_proximity import name as phenotype_proximity_name
from ..workflows.front_proximity import name as front_proximity_name
from ..workflows.density import name as density_name

workflows = {
    **diffusion_workflow,
    **phenotype_proximity_workflow,
    **front_proximity_workflow,
    **density_workflow,
}

workflow_names = [
    diffusion_name,
    phenotype_proximity_name,
    front_proximity_name,
    density_workflow_name,
]

config_filename = '.spt_pipeline.json'

def get_version():
    with importlib.resources.path('spatialprofilingtoolbox', 'version.txt') as path:
        with open(path, 'r') as file:
            version = file.read().rstrip('\n')
    return version
