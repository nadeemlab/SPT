elementary_phenotypes_file_identifier = 'Elementary phenotypes file'
composite_phenotypes_file_identifier = 'Complex phenotypes file'
compartments_file_identifier = 'Compartments file'
default_file_manifest_filename = 'file_manifest.tsv'
default_db_config_filename = '.spt_db.config'
expressions_index_filename = 'expressions_index.json'

from importlib.metadata import version

def get_version():
    return version('spatialprofilingtoolbox')
