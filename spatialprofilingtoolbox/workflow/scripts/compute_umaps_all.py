"""Convenience utility to compute UMAPs for all studies in the database."""
import subprocess
import argparse
from importlib.resources import as_file
from importlib.resources import files

from spatialprofilingtoolbox.db.database_connection import get_and_validate_database_config
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument

def main():
    parser = argparse.ArgumentParser(
        prog='spt workflow compute-umaps-all',
        description='Compute UMAPs for all studies.',
    )
    add_argument(parser, 'database config')

    args = parser.parse_args()
    try:
        config_file = get_and_validate_database_config(args)
    except FileNotFoundError:
        print("Did not find supplied database config file, trying local default.")
        local_default = '~/.spt_db.config.local'
        config_file = get_and_validate_database_config({'database_config_file': local_default})
    _files = files('spatialprofilingtoolbox.workflow.assets').joinpath('compute_umaps_all.sh')
    with as_file(_files) as path:
        subprocess.run(['bash', str(path), 'umap_runs', config_file], check=True)

if __name__ == '__main__':
    main()
