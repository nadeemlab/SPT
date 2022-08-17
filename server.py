#!/usr/bin/env python3
import argparse
import os
from os.path import join
from os.path import exists
from os.path import abspath
from os.path import expanduser
import re
import random
import socketserver

import spatialprofilingtoolbox
from spatialprofilingtoolbox.environment.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.environment.logging.log_formats import colorized_logger
logger = colorized_logger('spt-counts-server')

data_array_filename = 'expression_data_array.b'

class CompressedMatrix:
    def __init__(self, database_config_file):
        dcm = DatabaseConnectionMaker(database_config_file)
        connection = dcm.get_connection()
        self.binary_values_array = self.retrieve_data_array(connection)
        connection.close()

    def retrieve_data_array(self, connection):
        with connection.cursor() as cursor:
            cursor.execute(self.get_sparse_matrix_query())
            sparse_entries = cursor.fetchall()

        logger.debug('Received %s sparse entries from db.', len(sparse_entries))
        sparse_entries.sort(key = lambda x: x[0])
        logger.debug('Sorted entries by structure identifier.')
        number_cells = self.get_number_cells(sparse_entries)
        logger.debug('Unique structures: %s', number_cells)
        target_index_lookup = self.get_target_index_lookup(sparse_entries)
        logger.debug('Unique channels: %s', len(target_index_lookup))
        logger.debug('Channel index assignments: %s', target_index_lookup)

        data_array = [0] * number_cells
        logger.debug('Allocated data array.')
        self.fill_data_array(data_array, sparse_entries, target_index_lookup)
        subsample = 30
        logger.debug('%s randomly sampled vectors:', subsample)
        for i in range(subsample):
            value = data_array[random.choice(range(len(data_array)))]
            print(''.join(list(reversed(re.sub('0', ' ', f'{value:064b}')))))
        logger.debug('Sorting for consistency.')
        data_array.sort(reverse=True)
        logger.debug('Done')
        self.write_data_array_to_file(data_array)
        number_mb = int(len(data_array) * 8 / 1000000)
        logger.debug('Wrote %s MB to %s .', number_mb, data_array_filename)

        logger.debug('Count in test case.')
        signature = 27
        count = self.count_structures_of_signatures(signature, data_array)
        logger.debug('Finished counting test case, got: %s', count)
        signature2 = random.choice(data_array)
        count = self.count_structures_of_signatures(signature2, data_array)
        logger.debug('Case %s, got: %s', signature2, count)
        signature3 = random.choice(data_array)
        count = self.count_structures_of_signatures(signature3, data_array)
        logger.debug('Case %s, got: %s', signature3, count)

    def get_sparse_matrix_query(self):
        return '''
        SELECT histological_structure, target, CASE WHEN discrete_value='positive' THEN 1 ELSE 0 END AS coded_value
        FROM
        expression_quantification
        ;
        '''

    def get_number_cells(self, sparse_entries_sorted):
        count = 1
        for i in range(len(sparse_entries_sorted) -1):
            if sparse_entries_sorted[i][0] != sparse_entries_sorted[i+1][0]:
                count = count + 1
        return count

    def get_target_index_lookup(self, sparse_entries_sorted):
        targets = set([])
        for i in range(len(sparse_entries_sorted)):
            targets.add(sparse_entries_sorted[i][1])
        targets = sorted(list(targets))
        lookup = {
            target : i
            for i, target in enumerate(targets)
        }
        return lookup

    def fill_data_array(self, data_array, entries, target_index_lookup):
        structure_index = 0
        for i in range(len(entries)):
            if i > 0:
                if entries[i][0] != entries[i-1][0]:
                    structure_index = structure_index + 1
            if entries[i][2] == 1:
                data_array[structure_index] = data_array[structure_index] + (1 << target_index_lookup[entries[i][1]])

    def write_data_array_to_file(self, data_array):
        with open(data_array_filename, 'wb') as file:
            for entry in data_array:
                file.write(entry.to_bytes(8, 'little'))

    def count_structures_of_signatures(self, signature, data_array):
        count = 0
        for entry in data_array:
            if entry == signature:
                count = count + 1
        return count


class Handler_TCPServer(socketserver.BaseRequestHandler):
    """
    The TCP Server class for demonstration.

    Note: We need to implement the Handle method to exchange data
    with TCP client.

    """
    def handle(self):
        # self.request - TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print("{} sent:".format(self.client_address[0]))
        print(self.data)
        print(my_setup_data)
        # just send back ACK for data arrival confirmation
        self.request.sendall("ACK from TCP Server".encode())

if __name__ == "__main__":
    # HOST, PORT = "localhost", 9999

    # # Init the TCP server object, bind it to the localhost on 9999 port
    # tcp_server = socketserver.TCPServer((HOST, PORT), Handler_TCPServer)

    # # Activate the TCP server.
    # # To abort the TCP server, press Ctrl-C.
    # tcp_server.serve_forever()


    parser = argparse.ArgumentParser(
        description = 'Server providing counts of samples satisfying given partial signatures.'
    )
    parser.add_argument(
        '--database-config-file',
        dest='database_config_file',
        type=str,
        required=True,
        help='Provide the file for database configuration.',
    )
    args = parser.parse_args()
    database_config_file = abspath(expanduser(args.database_config_file))
    # with CountsServer(database_config_file) as server:
    #     server.loop()

    cm = CompressedMatrix(database_config_file)
