import importlib.resources

from ..workflows.density import components as density_workflow
from ..workflows.phenotype_proximity import components as phenotype_proximity_workflow
from ..workflows.front_proximity import components as front_proximity_workflow

workflows = {
    **density_workflow,
    **phenotype_proximity_workflow,
    **front_proximity_workflow,
}

workflow_names = list(workflow.keys())

config_filename = '.spt_pipeline.json'

def get_version():
    with importlib.resources.path('spatialprofilingtoolbox', 'version.txt') as path:
        with open(path, 'r') as file:
            version = file.read().rstrip('\n')
    return version
