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
version = get_file_contents(join('spatialprofilingtoolbox', 'version.txt'))
requirements = get_file_contents(join('spatialprofilingtoolbox', 'requirements.txt')).rstrip('\n').split('\n')

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
        'spatialprofilingtoolbox.workflows.defaults',
        'spatialprofilingtoolbox.workflows.phenotype_proximity',
        'spatialprofilingtoolbox.workflows.front_proximity',
        'spatialprofilingtoolbox.workflows.density',
        'spatialprofilingtoolbox.workflows.nearest_distance',
        'spatialprofilingtoolbox.workflows.halo_import',
        'spatialprofilingtoolbox.environment',
        'spatialprofilingtoolbox.environment.logging',
        'spatialprofilingtoolbox.environment.source_file_parsers',
        'spatialprofilingtoolbox.applications',
        'spatialprofilingtoolbox.applications.front_proximity_viz',
        'spatialprofilingtoolbox.templates',
        'spatialprofilingtoolbox.data_model',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Scientific/Engineering',
        'Intended Audience :: Science/Research',
    ],
    package_data={
        'spatialprofilingtoolbox': [
            'version.txt',
            'requirements.txt',
        ],
        'spatialprofilingtoolbox.workflows': [
            'main.nf.jinja',
        ],
        'spatialprofilingtoolbox.templates': [
            'nextflow.config.jinja',
            'log_table.tex.jinja',
            'log_table.html.jinja',
            '.spt_db.config.template',
        ],
        'spatialprofilingtoolbox.data_model': [
            'fields.tsv',
            'pathology_schema.sql',
        ]
    },
    python_requires='>=3.7',
    scripts=[
        'spatialprofilingtoolbox/scripts/spt-configure',
        'spatialprofilingtoolbox/scripts/spt-generate-run-information',
        'spatialprofilingtoolbox/scripts/spt-query-for-file',
        'spatialprofilingtoolbox/scripts/spt-extract-compartments',
        'spatialprofilingtoolbox/scripts/spt-report-run-configuration',        
        'spatialprofilingtoolbox/scripts/spt-initialize',
        'spatialprofilingtoolbox/scripts/spt-core-job',
        'spatialprofilingtoolbox/scripts/spt-aggregate-core-results',
        'spatialprofilingtoolbox/scripts/spt-merge-sqlite-dbs',
        'spatialprofilingtoolbox/scripts/spt-merge-performance-reports',
        'spatialprofilingtoolbox/scripts/spt-front-proximity-viz',
        'spatialprofilingtoolbox/scripts/spt-print',
        'spatialprofilingtoolbox/scripts/spt-report-on-logs',
        'spatialprofilingtoolbox/scripts/spt-guess-channels',
        'spatialprofilingtoolbox/scripts/spt-generate-aws-task-definition',
    ],
    install_requires=requirements,
    project_urls = {
        'Documentation': 'https://spatialprofilingtoolbox.readthedocs.io/en/prerelease/readme.html',
        'Source code': 'https://github.com/nadeemlab/SPT'
    },
    url = 'https://spatialprofilingtoolbox.readthedocs.io/en/prerelease/readme.html',
)
