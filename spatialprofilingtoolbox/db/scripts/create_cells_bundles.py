"""Utility to pre-create cell data JSON payloads for application/client-use and save them to the database."""
import argparse

from psycopg2 import cursor as Psycopg2Cursor

from spatialprofilingtoolbox.db.database_connection import get_and_validate_database_config
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import retrieve_study_names

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt db create-cells-bundles')

class CellsDataBundler:
    database_config_file: str
    def __init__(self, database_config_file: str):
        self.database_config_file = database_config_file

    def precreate_cells_data(self, study: str, row: tuple) -> None:
        config = self.database_config_file
        bundle = self._get_bundle(study, bytearray(row[1]))
        with DBCursor(database_config_file=config, study=study) as writing_cursor:
            insert_query = '''
                INSERT INTO
                ondemand_studies_index (
                    specimen,
                    blob_type,
                    blob_contents
                )
                VALUES (%s, %s, %s) ;
            '''
            writing_cursor.execute(insert_query, (row[0], 'json_cells_data', bundle.encode('utf-8')))
            logger.info(f'Wrote cells data for "{row[0]}" ({study})')

    def _get_bundle(self, study: str, feature_matrix_blob: bytearray) -> str:
        df0 = 

        df = self.data_arrays[measurement_study][sample].drop('integer', axis=1).reset_index()

        additional = ['histological_structure_id', 'pixel x', 'pixel y']
        feature_names = sorted(list(set(list(df.columns)).difference(set(additional))))
        feature_names = additional + feature_names
        logger.debug(f'Forming JSON for cells dataframe of shape {df.shape} for {sample}.')
        return f'''{{
            "feature_names": {dumps(feature_names)},
            "cells": {df[feature_names].to_json(orient='values')}
        }}
        '''

def main():
    parser = argparse.ArgumentParser(
        prog='spt db create-cells-bundles',
        description='Pre-create cell data JSON payloads and upload to database as blobs.'
    )
    add_argument(parser, 'database config')
    args = parser.parse_args()

    config_file = get_and_validate_database_config(args)
    studies = retrieve_study_names(config_file)
    bundler = CellsDataBundler(config_file)
    for study in studies:
        with DBCursor(database_config_file=config_file, study=study) as cursor:
            query = ''''
            SELECT specimen, blob_contents
            FROM ondemand_studies_index osi
            WHERE osi.blob_type='feature_matrix'
            '''
            cursor.execute(query)
            row = ()
            while row is not None:
                row = cursor.fetchone()
                bundler.precreate_cells_data(study, row)

if __name__ == '__main__':
    main()
