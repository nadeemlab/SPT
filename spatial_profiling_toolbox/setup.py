import setuptools
import os
import re

def get_property(prop, project):
    result = re.search(r'{}\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop), open(project + '/__init__.py').read())
    return result.group(1)

dir = os.path.dirname(__file__)

with open(os.path.join(dir, 'README.md'), 'r', encoding='utf-8') as fh:
    long_description = fh.read()

with open(os.path.join(dir, 'requirements.txt'), 'r', encoding='utf-8') as fh:
    requirements = fh.read().split('\n')

version = get_property('__version__', 'spatial_profiling_toolbox')
setuptools.setup(
    name='spatial-profiling-toolbox',
    version=version,
    author='Rami Vanguri, James Mathews',
    author_email='vangurir@mskcc.org',
    description='Toolbox for spatial analysis of pathology imaging.',
    long_description=long_description,
    packages=[
        'spatial_profiling_toolbox',
        'spatial_profiling_toolbox.dataset_designs',
        'spatial_profiling_toolbox.dataset_designs.multiplexed_immunofluorescence',
        'spatial_profiling_toolbox.workflows',
        'spatial_profiling_toolbox.workflows.diffusion',
        'spatial_profiling_toolbox.workflows.phenotype_proximity',
        'spatial_profiling_toolbox.environment',
        'spatial_profiling_toolbox.scripts',
        'spatial_profiling_toolbox.applications',
        'spatial_profiling_toolbox.applications.cell_cartoons',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    python_requires='>=3.7',
    scripts=[
        'spatial_profiling_toolbox/scripts/spt-pipeline',
        'spatial_profiling_toolbox/scripts/spt-analyze-results',
        'spatial_profiling_toolbox/scripts/spt_generate_jobs.py',
        'spatial_profiling_toolbox/scripts/spt_diffusion_analysis.py',
        'spatial_profiling_toolbox/scripts/spt_cell_phenotype_proximity_analysis.py',
        'spatial_profiling_toolbox/scripts/spt_print.py',
    ],
    install_requires=requirements,
)
