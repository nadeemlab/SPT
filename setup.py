import setuptools
import os
from os.path import join, dirname

def get_file_contents(filename):
    package_directory = dirname(__file__)
    with open(join(package_directory, filename), 'r', encoding='utf-8') as file:
        contents = file.read()
    return contents

long_description = """See the [user documentation](https://github.com/nadeemlab/SPT).
"""
requirements = [
    'Cython==0.29.23',
    'matplotlib==3.4.2',
    'pyparsing==2.4.7',
    'python-dateutil==2.8.1',
    'pytz==2021.1',
    'six==1.16.0',
    'networkx==2.5.1',
    'POT==0.7.0',
    'seaborn==0.11.1',
    'plotly==5.1.0',
    'kaleido==0.2.1',
    'numpy==1.21.0',
    'pandas>=1.1.5',
    'scipy==1.7.1',
    'scikit-learn==0.24.1',
]
version = get_file_contents(join('spatialprofilingtoolbox', 'version.txt'))

setuptools.setup(
    name='spatialprofilingtoolbox',
    version=version,
    author='Rami Vanguri, James Mathews',
    author_email='mathewj2@mskcc.org',
    description='Toolbox for spatial analysis of pathology images.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=[
        'spatialprofilingtoolbox',
        'spatialprofilingtoolbox.dataset_designs',
        'spatialprofilingtoolbox.dataset_designs.multiplexed_imaging',
        'spatialprofilingtoolbox.workflows',
        'spatialprofilingtoolbox.workflows.diffusion',
        'spatialprofilingtoolbox.workflows.phenotype_proximity',
        'spatialprofilingtoolbox.workflows.front_proximity',
        'spatialprofilingtoolbox.workflows.density',
        'spatialprofilingtoolbox.environment',
        'spatialprofilingtoolbox.applications',
        'spatialprofilingtoolbox.applications.configuration_ui',
        'spatialprofilingtoolbox.applications.cell_cartoons',
        'spatialprofilingtoolbox.applications.diffusion_tests_viz',
        'spatialprofilingtoolbox.applications.diffusion_graphs_viz',
        'spatialprofilingtoolbox.applications.front_proximity_viz',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Scientific/Engineering',
        'Intended Audience :: Science/Research',
    ],
    package_data={'spatialprofilingtoolbox': [
            'version.txt',
            'spt_pipeline.nf',
            'nextflow.config.lsf',
            'nextflow.config.local',
        ]},
    python_requires='>=3.7',
    scripts=[
        'spatialprofilingtoolbox/scripts/spt-pipeline',
        'spatialprofilingtoolbox/scripts/spt-merge-sqlite-dbs',
        'spatialprofilingtoolbox/scripts/spt-diffusion-viz',
        'spatialprofilingtoolbox/scripts/spt-diffusion-graphs-viz',
        'spatialprofilingtoolbox/scripts/spt-front-proximity-viz',
        'spatialprofilingtoolbox/scripts/spt-print',
        'spatialprofilingtoolbox/scripts/spt-aggregate-cell-data',
    ],
    install_requires=requirements,
    project_urls = {
        'Documentation': 'https://spatialprofilingtoolbox.readthedocs.io/en/prerelease/readme.html',
        'Source code': 'https://github.com/nadeemlab/SPT'
    },
    url = 'https://spatialprofilingtoolbox.readthedocs.io/en/prerelease/readme.html',
)
