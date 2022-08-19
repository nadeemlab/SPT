import importlib.resources

elementary_phenotypes_file_identifier = 'Elementary phenotypes file'
composite_phenotypes_file_identifier = 'Complex phenotypes file'
compartments_file_identifier = 'Compartments file'
default_file_manifest_filename = 'file_manifest.tsv'
default_db_config_filename = '.spt_db.config'
data_array_filename = 'expression_data_array.bin'
channel_lookup_filename = 'channel_lookup.json'

def get_version():
    with importlib.resources.path('spatialprofilingtoolbox', 'version.txt') as path:
        with open(path, 'r') as file:
            version = file.read().rstrip('\n')
    return version
