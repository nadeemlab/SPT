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
        'spatialprofilingtoolbox.entry_point',
        'spatialprofilingtoolbox.apiserver',
        'spatialprofilingtoolbox.apiserver.scripts',
        'spatialprofilingtoolbox.control',
        'spatialprofilingtoolbox.control.scripts',
        'spatialprofilingtoolbox.countsserver',
        'spatialprofilingtoolbox.countsserver.scripts',
        'spatialprofilingtoolbox.dashboard',
        'spatialprofilingtoolbox.dashboard.scripts',
        'spatialprofilingtoolbox.db',
        'spatialprofilingtoolbox.db.scripts',
        'spatialprofilingtoolbox.db.data_model',
        'spatialprofilingtoolbox.workflow',
        'spatialprofilingtoolbox.workflow.scripts',
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
        ],
        'spatialprofilingtoolbox.entry_point': [
            'spt-completion.sh',
        ],
        'spatialprofilingtoolbox.apiserver': [
            'version.txt',
        ],
        'spatialprofilingtoolbox.countsserver': [
            'version.txt',
        ],
        'spatialprofilingtoolbox.workflow': [
            'version.txt',
        ],
        'spatialprofilingtoolbox.workflow.scripts': [
            'version.txt.py',
            'aggregate-core-results.py',
            'core-job.py',
            'extract-compartments.py',
            'generate-run-information.py',
            'initialize.py',
            'merge-performance-reports.py',
            'merge-sqlite-dbs.py',
            'report-run-configuration.py',
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
        'spatialprofilingtoolbox.control.scripts' : [
            'configure.py',
            'guess-channels.py',
            'report-on-logs.py',
        ],
        'spatialprofilingtoolbox.countsserver.scripts' : [
            'read-expression-dump-file.py',
            'cache-expressions-data-array.py',
            'start.py',
        ],
        'spatialprofilingtoolbox.db.scripts' : [
            'create-schema.py',
            'modify-constraints.py',
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
    data_files=[
        ('/etc/bash_completion.d', ['spatialprofilingtoolbox/entry_point/spt-completion.sh']),
    ],
    python_requires='>=3.9',
    entry_points={
        'console_scripts' : [
            'spt = spatialprofilingtoolbox.entry_point.spt:main_program',
            'spt-enable-completion = spatialprofilingtoolbox.entry_point.spt_enable_completion:main_program',
        ]
    },
    install_requires=[
        'psycopg2-binary==2.9.3',
    ],
    extras_require={
        'apiserver': ['fastapi>=0.68.0,<0.69.0', 'uvicorn>=0.15.0,<0.16.0'],
        'control': ['Jinja2==3.0.1', 'pandas>=1.1.5'],
        'countsserver': [''],
        'dashboard': ['Jinja2==3.0.1'],
        'db': ['pandas>=1.1.5'],
        'workflow': ['numpy==1.22.3', 'scipy==1.8.0', 'scikit-learn==0.24.1', 'pyshp==2.2.0', 'pandas>=1.1.5'],
        'all' : ['fastapi>=0.68.0,<0.69.0', 'uvicorn>=0.15.0,<0.16.0', 'Jinja2==3.0.1', 'pandas>=1.1.5', 'numpy==1.22.3', 'scipy==1.8.0', 'scikit-learn==0.24.1', 'pyshp==2.2.0'],
    },
    project_urls = {
        'Documentation': 'https://github.com/nadeemlab/SPT',
        'Source code': 'https://github.com/nadeemlab/SPT'
    },
    url = 'https://github.com/nadeemlab/SPT',
)
