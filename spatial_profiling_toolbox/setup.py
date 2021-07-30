import setuptools
import os
from os.path import join, dirname
import re

def get_file_contents(filename):
    package_directory = dirname(__file__)
    with open(join(package_directory, filename), 'r', encoding='utf-8') as file:
        contents = file.read()
    return contents

long_description = get_file_contents('README.md')
requirements = [
    'cycler==0.10.0',
    'Cython==0.29.23',
    'kiwisolver==1.3.1',
    'matplotlib==3.4.2',
    'numpy==1.21.0',
    'pandas==1.1.5',
    'Pillow==8.2.0',
    'POT==0.7.0',
    'pyparsing==2.4.7',
    'python-dateutil==2.8.1',
    'pytz==2021.1',
    'scipy==1.7.0',
    'seaborn==0.11.1',
    'six==1.16.0',
    'plotly==5.1.0',
    'networkx==2.5.1',
    'kaleido==0.2.1',
]
version = get_file_contents(join('spatial_profiling_toolbox', 'version.txt'))

setuptools.setup(
    name='spatial-profiling-toolbox',
    version=version,
    author='Rami Vanguri, James Mathews',
    author_email='mathewj2@mskcc.org',
    description='Toolbox for spatial analysis of pathology imaging.',
    long_description=long_description,
    packages=[
        'spatial_profiling_toolbox',
        'spatial_profiling_toolbox.dataset_designs',
        'spatial_profiling_toolbox.dataset_designs.multiplexed_imaging',
        'spatial_profiling_toolbox.workflows',
        'spatial_profiling_toolbox.workflows.diffusion',
        'spatial_profiling_toolbox.workflows.phenotype_proximity',
        'spatial_profiling_toolbox.environment',
        'spatial_profiling_toolbox.scripts',
        'spatial_profiling_toolbox.applications',
        'spatial_profiling_toolbox.applications.cell_cartoons',
        'spatial_profiling_toolbox.applications.diffusion_tests_viz',
        'spatial_profiling_toolbox.applications.diffusion_graphs_viz',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    package_data={'spatial_profiling_toolbox': ['version.txt']},
    python_requires='>=3.7',
    scripts=[
        'spatial_profiling_toolbox/scripts/spt-pipeline',
        'spatial_profiling_toolbox/scripts/spt-analyze-results',
        'spatial_profiling_toolbox/scripts/spt-diffusion-viz',
        'spatial_profiling_toolbox/scripts/spt-diffusion-graphs-viz',
        'spatial_profiling_toolbox/scripts/spt-print',
        'spatial_profiling_toolbox/scripts/spt_generate_jobs.py',
        'spatial_profiling_toolbox/scripts/spt_diffusion_analysis.py',
        'spatial_profiling_toolbox/scripts/spt_cell_phenotype_proximity_analysis.py',
    ],
    install_requires=requirements,
)
