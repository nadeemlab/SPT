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
    author='James Mathews',
    author_email='mathewj2@mskcc.org',
    description='Toolbox for spatial analysis of single-cell images.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=[
        'spatialprofilingtoolbox',
        'spatialprofilingtoolbox.apiserver',
        'spatialprofilingtoolbox.control',
        'spatialprofilingtoolbox.countsserver',
        'spatialprofilingtoolbox.dashboard',
        'spatialprofilingtoolbox.db',
        'spatialprofilingtoolbox.db.data_model',
        'spatialprofilingtoolbox.workflow.dataset_designs',
        'spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging',
        'spatialprofilingtoolbox.workflow.workflows',
        'spatialprofilingtoolbox.workflow.workflows.defaults',
        'spatialprofilingtoolbox.workflow.workflows.phenotype_proximity',
        'spatialprofilingtoolbox.workflow.workflows.front_proximity',
        'spatialprofilingtoolbox.workflow.workflows.density',
        'spatialprofilingtoolbox.workflow.workflows.nearest_distance',
        'spatialprofilingtoolbox.workflow.workflows.halo_import',
        'spatialprofilingtoolbox.workflow.environment',
        'spatialprofilingtoolbox.workflow.environment.logging',
        'spatialprofilingtoolbox.workflow.environment.source_file_parsers',
        'spatialprofilingtoolbox.workflow.templates',
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
        'spatialprofilingtoolbox.apiserver': [
            'version.txt',
        ],
        'spatialprofilingtoolbox.countsserver': [
            'version.txt',
        ],
        'spatialprofilingtoolbox.workflow': [
            'version.txt',
            'scripts/aggregate-core-results',
            'scripts/core-job',
            'scripts/extract-compartments',
            'scripts/generate-run-information',
            'scripts/initialize',
            'scripts/merge-performance-reports',
            'scripts/merge-sqlite-dbs',
            'scripts/report-run-configuration',
        ],
        'spatialprofilingtoolbox.workflow.workflows': [
            'main.nf.jinja',
        ],
        'spatialprofilingtoolbox.workflow.templates': [
            'nextflow.config.jinja',
            'log_table.tex.jinja',
            'log_table.html.jinja',
            '.spt_db.config.template',
        ],
        'spatialprofilingtoolbox.control' : [
            'scripts/configure',
            'scripts/guess-channels',
            'scripts/report-on-logs',
        ],
        'spatialprofilingtoolbox.countsserver' : [
            'scripts/read-expression-dump-file',
            'scripts/cache-expressions-data-array',
            'scripts/start',
        ],
        'spatialprofilingtoolbox.db' : [
            'scripts/create-schema',
            'scripts/modify-constraints',
        ],
        'spatialprofilingtoolbox.db.data_model': [
            'create_roles.sql',
            'create_views.sql',
            'drop_views.sql',
            'fields.tsv',
            'grant_on_tables.sql',
            'pathology_schema.sql',
            'performance_tweaks.sql',
            'refresh_views.sql',
        ],
    },
    python_requires='>=3.7',
    scripts=[
        'spatialprofilingtoolbox/scripts/spt',
    ],
    install_requires=requirements,
    project_urls = {
        'Documentation': 'https://github.com/nadeemlab/SPT',
        'Source code': 'https://github.com/nadeemlab/SPT'
    },
    url = 'https://github.com/nadeemlab/SPT',
)
