from os.path import exists
from os.path import join
from os import mkdir
import sqlite3

from common import generated_artifacts_directory

curated_dataset_file = 'example_curated_dataset.db'

def initialize_sqlite_db():
    connection = get_sqlite_connection()

def get_sqlite_connection():
    if not exists(generated_artifacts_directory):
        mkdir(generated_artifacts_directory)
    return sqlite3.connect(join(generated_artifacts_directory, curated_dataset_file))
