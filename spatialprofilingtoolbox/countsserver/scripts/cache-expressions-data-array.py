import argparse
import os
from os.path import join
from os.path import exists
from os.path import abspath
from os.path import expanduser
import re
import random
import json

import spatialprofilingtoolbox
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
logger = colorized_logger('cache-expressions-data-array')


class CompressedMatrixPuller:
    def __init__(self, database_config_file):
        dcm = DatabaseConnectionMaker(database_config_file)
        connection = dcm.get_connection()
        self.retrieve_data_arrays(connection)
        connection.close()
        self.write_data_arrays()
        self.write_index()
        self.report_subsample_for_inspection()

    def retrieve_data_arrays(self, connection):
        study_names = self.get_study_names(connection)
        self.studies = {}
        for study_name in study_names:
            sparse_entries = self.get_sparse_entries(connection, study_name)
            data_arrays_by_specimen, target_index_lookup = self.parse_data_arrays_by_specimen(sparse_entries)
            self.studies[study_name] = {
                'data arrays by specimen' : data_arrays_by_specimen,
                'target index lookup' : target_index_lookup,
                'target by symbol' : self.get_target_by_symbol(connection),
            }

    def get_study_names(self, connection):
        with connection.cursor() as cursor:
            cursor.execute('SELECT name FROM specimen_measurement_study ;')
            rows = cursor.fetchall()
        return [row[0] for row in rows]

    def get_sparse_entries(self, connection, study_name):
        sparse_entries = []
        with connection.cursor() as cursor:
            cursor.execute(self.get_sparse_matrix_query(), (study_name,))
            total = cursor.rowcount
            while cursor.rownumber < total - 1:
                current_number_stored = len(sparse_entries)
                sparse_entries.extend(cursor.fetchmany(size=self.get_batch_size()))
                logger.debug('Received %s entries from DB.', len(sparse_entries) - current_number_stored)
        logger.debug('Received %s sparse entries total from DB.', len(sparse_entries))
        return sparse_entries

    def get_sparse_matrix_query(self):
        return '''
        SELECT
        eq.histological_structure,
        eq.target,
        CASE WHEN discrete_value='positive' THEN 1 ELSE 0 END AS coded_value,
        sdmp.specimen as specimen
        FROM expression_quantification eq
        JOIN histological_structure hs ON eq.histological_structure=hs.identifier
        JOIN histological_structure_identification hsi ON hs.identifier=hsi.histological_structure
        JOIN data_file df ON hsi.data_source=df.sha256_hash
        JOIN specimen_data_measurement_process sdmp ON df.source_generation_process=sdmp.identifier
        WHERE sdmp.study=%s
        ORDER BY sdmp.specimen, eq.histological_structure, eq.target
        ;
        '''

    def get_batch_size(self):
        return 10000000

    def parse_data_arrays_by_specimen(self, sparse_entries):
        target_index_lookup = self.get_target_index_lookup(sparse_entries)
        sparse_entries.sort(key = lambda x: (x[3], x[0]))
        data_arrays_by_specimen = {}
        last_index = len(sparse_entries) - 1
        specimen = sparse_entries[0][3]
        buffer = []
        cell_count = 1
        for i in range(len(sparse_entries)):
            buffer.append(sparse_entries[i])
            if (i != last_index) and (specimen == sparse_entries[i + 1][3]):
                if sparse_entries[i][0] != sparse_entries[i + 1][0]:
                    cell_count = cell_count + 1
            else:
                data_arrays_by_specimen[specimen] = [0] * cell_count
                self.fill_data_array(data_arrays_by_specimen[specimen], buffer, target_index_lookup)
                data_arrays_by_specimen[specimen].sort(reverse=True)
                number_mb = int(100 * len(data_arrays_by_specimen[specimen]) * 8 / 1000000) / 100
                logger.debug('Data array is %s MB for %s cells in specimen %s .', number_mb, cell_count, specimen)
                if i != last_index:
                    specimen = sparse_entries[i + 1][3]
                    buffer = []
                    cell_count = 1
        return data_arrays_by_specimen, target_index_lookup

    def get_target_index_lookup(self, sparse_entries):
        targets = set([])
        for i in range(len(sparse_entries)):
            targets.add(sparse_entries[i][1])
        targets = sorted(list(targets))
        lookup = {
            target : i
            for i, target in enumerate(targets)
        }
        logger.debug('Unique channels: %s', len(lookup))
        logger.debug('Channel index assignments: %s', lookup)
        return lookup

    def get_target_by_symbol(self, connection):
        query = '''
        SELECT identifier, symbol FROM chemical_species;
        '''
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
        target_by_symbol = {
            row[1] : row[0]
            for row in rows
        }
        logger.debug('Target by symbol: %s', target_by_symbol)
        return target_by_symbol

    def fill_data_array(self, data_array, entries, target_index_lookup):
        structure_index = 0
        for i in range(len(entries)):
            if i > 0:
                if entries[i][0] != entries[i-1][0]:
                    structure_index = structure_index + 1
            if entries[i][2] == 1:
                data_array[structure_index] = data_array[structure_index] + (1 << target_index_lookup[entries[i][1]])

    def write_data_arrays(self):
        study_names, study_indices = self.get_study_names_and_indices()
        for study_name, study in self.studies.items():
            study_index = study_indices[study_name]
            specimen, specimen_indices = self.get_specimens_and_indices(study_name)
            for specimen, data_array in study['data arrays by specimen'].items():
                specimen_index = specimen_indices[specimen]
                filename = '.'.join([
                    self.get_data_array_filename_base(),
                    str(study_index),
                    str(specimen_index),
                    'bin',
                ])
                self.write_data_array_to_file(data_array, filename)

    def write_index(self):
        index = []
        study_names, study_indices = self.get_study_names_and_indices()
        for study_name, study in self.studies.items():
            index_item = {}
            index_item['specimen measurement study name'] = study_name
            index_item['expressions files'] = []
            study_index = study_indices[study_name]
            specimen, specimen_indices = self.get_specimens_and_indices(study_name)
            for specimen, data_array in study['data arrays by specimen'].items():
                specimen_index = specimen_indices[specimen]
                filename = '.'.join([
                    self.get_data_array_filename_base(),
                    str(study_index),
                    str(specimen_index),
                    'bin',
                ])
                index_item['expressions files'].append({
                    'specimen' : specimen,
                    'filename' : filename,
                })
            index_item['target index lookup'] = study['target index lookup']
            index_item['target by symbol'] = study['target by symbol']
            index.append(index_item)
        with open(expressions_index_filename, 'wt') as index_file:
            index_file.write(json.dumps({'' : index}, indent=4))
        logger.debug('Wrote expression index file %s .', expressions_index_filename)

    def get_study_names_and_indices(self):
        study_names = sorted(list(self.studies.keys()))
        return study_names, { s : i for i, s in enumerate(study_names)}

    def get_specimens_and_indices(self, study_name):
        study = self.studies[study_name]
        specimens = sorted(list(study['data arrays by specimen'].keys()))
        return [
            specimens,
            { s : i for i, s in enumerate(specimens)},
        ]

    def get_data_array_filename_base(self):
        return 'expression_data_array'

    def write_data_array_to_file(self, data_array, filename):
        with open(filename, 'wb') as file:
            for entry in data_array:
                file.write(entry.to_bytes(8, 'little'))

    def report_subsample_for_inspection(self):
        size = 20
        logger.debug('%s randomly sampled vectors:', size)
        study_name = list(self.studies.keys())[0]
        data_arrays = self.studies[study_name]['data arrays by specimen']
        data_array = list(data_arrays.values())[0]
        for i in range(size):
            value = data_array[random.choice(range(len(data_array)))]
            print(''.join(list(reversed(re.sub('0', ' ', f'{value:064b}')))))


if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog = 'spt countsserver cache-expressions-data-array',
        description = 'Server providing counts of samples satisfying given partial signatures.'
    )
    parser.add_argument(
        '--database-config-file',
        dest='database_config_file',
        type=str,
        help='Provide the file for database configuration.',
    )
    args = parser.parse_args()

    from spatialprofilingtoolbox.standalone_utilities.module_load_error import SuggestExtrasException
    try:
        from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
        from spatialprofilingtoolbox.countsserver.defaults import expressions_index_filename
    except ModuleNotFoundError as e:
        SuggestExtrasException(e, 'workflow')

    database_config_file = abspath(expanduser(args.database_config_file))
    puller = CompressedMatrixPuller(database_config_file)

