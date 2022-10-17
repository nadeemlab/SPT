import argparse
import json
import socketserver
import os
import re
from os.path import join
# import signal
# import _thread

import spatialprofilingtoolbox
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
logger = colorized_logger('spt countsserver start')


class CountsProvider:
    def __init__(self, data_directory):
        self.load_expressions_indices(data_directory)
        self.load_data_matrices(data_directory)
        logger.info('countsserver is ready to accept connections.')

    def load_expressions_indices(self, data_directory):
        logger.debug('Searching for source data in: %s', data_directory)
        json_files = [f for f in os.listdir(data_directory) if os.path.isfile(join(data_directory, f)) and re.search(r'\.json$', f)]
        if len(json_files) != 1:
            logger.error('Did not find index JSON file.')
            exit()
        with open(join(data_directory, json_files[0]), 'rt') as file:
            root = json.loads(file.read())
            entries = root[list(root.keys())[0]]
            self.studies = {}
            for entry in entries:
                self.studies[entry['specimen measurement study name']] = entry

    def load_data_matrices(self, data_directory):
        self.data_arrays = {}
        for study_name in self.get_study_names():
            self.data_arrays[study_name] = {
                item['specimen'] : self.get_data_array_from_file(join(data_directory, item['filename']))
                for item in self.studies[study_name]['expressions files']
            }

    def get_study_names(self):
        return self.studies.keys()

    def get_data_array_from_file(self, filename):
        data_array = []
        with open(filename, 'rb') as file:
            buffer = None
            while buffer != b'':
                buffer = file.read(8)
                data_array.append(int.from_bytes(buffer, 'little'))
        return data_array

    def compute_signature(self, channel_names, study_name):
        target_by_symbol = self.studies[study_name]['target by symbol']
        target_index_lookup = self.studies[study_name]['target index lookup']
        if not all([name in target_by_symbol.keys() for name in channel_names]):
            return None
        identifiers = [target_by_symbol[name] for name in channel_names]
        indices = [target_index_lookup[identifier] for identifier in identifiers]
        signature = 0
        for index in indices:
            signature = signature + (1 << index)
        return signature

    def count_structures_of_exact_signature(self, signature, study_name):
        counts = {}
        for specimen, data_array in self.data_arrays[study_name].items():
            count = 0
            for entry in data_array:
                if entry == signature:
                    count = count + 1
            counts[specimen] = [count, len(data_array)]
        return counts

    def count_structures_of_partial_signature(self, signature, study_name):
        counts = {}
        for specimen, data_array in self.data_arrays[study_name].items():
            count = 0
            for entry in data_array:
                if entry | signature == entry:
                    count = count + 1
            counts[specimen] = [count, len(data_array)]
        return counts

    def count_structures_of_partial_signed_signature(self, positives_signature, negatives_signature, study_name):
        counts = {}
        for specimen, data_array in self.data_arrays[study_name].items():
            count = 0
            for entry in data_array:
                if (entry | positives_signature == entry) and (~entry | negatives_signature == ~entry):
                    count = count + 1
            counts[specimen] = [count, len(data_array)]
        return counts

    def get_status(self):
        return [
            {
                'study' : study_name,
                'counts by channel' : [
                    {
                        'channel symbol' : symbol,
                        'count' : self.count_structures_of_partial_signed_signature([symbol], [], study_name),
                    }
                    for symbol in sorted(list(targets['target by symbol'].keys()))
                ],
                'total number of cells' : len(self.data_arrays[study_name]),
            }
            for study_name, targets in self.studies.items()
        ]

    def has_study(self, study_name):
        return study_name in self.studies.keys()

class CountsRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(512).strip()
        print('Request:')
        logger.info(data)
        if data == '':
            logger.info('Empty body. Serving status.')
            self.request.sendall((json.dumps(self.server.counts_provider.get_status(), indent=4) + self.get_end_of_transmission()).encode('utf-8'))
            return
        record_separator = chr(30)
        group_separator = chr(29)
        groups = data.decode('utf-8').split(group_separator)
        study_name = groups[0]
        positive_channel_names = groups[1].split(record_separator)
        negative_channel_names = groups[2].split(record_separator)
        if positive_channel_names == ['']:
            positive_channel_names = []
        if negative_channel_names == ['']:
            negative_channel_names = []
        logger.info('Study: %s' % study_name)
        logger.info('Positives: %s' % positive_channel_names)
        logger.info('Negatives: %s' % negative_channel_names)
        if not self.server.counts_provider.has_study(study_name):
            logger.error('Study not known to counts server: %s', study_name)
            self.request.sendall(''.encode('utf-8'))
            return
        positives_signature = self.server.counts_provider.compute_signature(positive_channel_names, study_name)
        negatives_signature = self.server.counts_provider.compute_signature(negative_channel_names, study_name)
        logger.info('Signature:')
        logger.info(positives_signature)
        logger.info(negatives_signature)
        if positives_signature is None:
            logger.error('Could not understand channel names as defining a signature: %s' % positive_channel_names) 
            self.request.sendall(''.encode('utf-8'))
            return
        if negatives_signature is None:
            logger.error('Could not understand channel names as defining a signature: %s' % negative_channel_names) 
            self.request.sendall(''.encode('utf-8'))
            return
        logger.info(f'{positives_signature:064b}')
        logger.info(f'{negatives_signature:064b}')
        counts = self.server.counts_provider.count_structures_of_partial_signed_signature(positives_signature, negatives_signature, study_name)
        self.request.sendall((json.dumps(counts) + self.get_end_of_transmission()).encode('utf-8'))

    def get_end_of_transmission(self):
        return chr(4)

# def server_shutdown(server):
#     server.shutdown()

# def initiate_shutdown(server):
#     logger.info('Shutting down counts server.')
#     _thread.start_new_thread(server_shutdown, (server,))

if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog = 'spt countsserver start',
        description = 'Server providing counts of samples satisfying given partial signatures.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--host',
        dest='host',
        type=str,
        default='localhost',
        help='The hostname or IP address on which to open the TCP socket.',
    )
    parser.add_argument(
        '--port',
        dest='port',
        type=int,
        default=8016,
        help='The port on which to open the TCP socket.',
    )
    parser.add_argument(
        '--source-data-location',
        dest='source_data_location',
        type=str,
        default='/countsserver/source_data/',
        help='The directory in which this process will search for expression data binaries and the JSON index file.',
    )
    args = parser.parse_args()

    counts_provider = CountsProvider(args.source_data_location)
    tcp_server = socketserver.TCPServer((args.host, args.port), CountsRequestHandler)
    tcp_server.counts_provider = counts_provider
    # signal.signal(signal.SIGTERM, lambda signum, frame: initiate_shutdown(tcp_server))
    # signal.signal(signal.SIGINT, lambda signum, frame: initiate_shutdown(tcp_server))
    tcp_server.serve_forever(poll_interval=0.2)

