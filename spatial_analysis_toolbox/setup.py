import setuptools
import os

dir = os.path.dirname(__file__)

with open(os.path.join(dir, 'README.md'), 'r', encoding='utf-8') as fh:
    long_description = fh.read()

with open(os.path.join(dir, 'requirements.txt'), 'r', encoding='utf-8') as fh:
    requirements = fh.read().split('\n')

setuptools.setup(
    name='spatial-analysis-toolbox',
    version='0.0.1',
    author='Rami Vanguri, James Mathews',
    author_email='vangurir@mskcc.org',
    description='Toolbox for spatial analysis of pathology imaging.',
    long_description=long_description,
    packages=[
        'spatial_analysis_toolbox',
        'spatial_analysis_toolbox.dataset_designs',
        'spatial_analysis_toolbox.dataset_designs.multiplexed_immunofluorescence',
        'spatial_analysis_toolbox.computation_modules',
        'spatial_analysis_toolbox.computation_modules.diffusion',
        'spatial_analysis_toolbox.computation_modules.phenotype_proximity',
        'spatial_analysis_toolbox.environment',
        'spatial_analysis_toolbox.scripts',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    python_requires='>=3.7',
    scripts=[
        'spatial_analysis_toolbox/scripts/sat-pipeline',
        'spatial_analysis_toolbox/scripts/sat-analyze-results',
        'spatial_analysis_toolbox/scripts/sat_generate_jobs.py',
        'spatial_analysis_toolbox/scripts/sat_diffusion_analysis.py',
        'spatial_analysis_toolbox/scripts/sat_cell_phenotype_proximity_analysis.py',
        'spatial_analysis_toolbox/scripts/sat_print.py',
    ],
    install_requires=requirements,
)
