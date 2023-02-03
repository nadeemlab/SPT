"""Entry point into the fast cell counts TCP server."""
import argparse
import json
import socketserver

from spatialprofilingtoolbox.countsserver.counts_provider import CountsProvider
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt countsserver start')


class CountsRequestHandler(socketserver.BaseRequestHandler):
    """The TCP server for fast cell counts."""
    def handle(self):
        data = self.request.recv(512).strip()
        print('Request:')
        logger.info(data)
        if data == '':
            logger.info('Empty body. Serving status.')
            self.request.sendall((json.dumps(self.server.counts_provider.get_status(
            ), indent=4) + self.get_end_of_transmission()).encode('utf-8'))
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
        logger.info('Study: %s', study_name)
        logger.info('Positives: %s', positive_channel_names)
        logger.info('Negatives: %s', negative_channel_names)
        if not self.server.counts_provider.has_study(study_name):
            logger.error('Study not known to counts server: %s', study_name)
            self.request.sendall(''.encode('utf-8'))
            return
        positives_signature = self.server.counts_provider.compute_signature(
            positive_channel_names, study_name)
        negatives_signature = self.server.counts_provider.compute_signature(
            negative_channel_names, study_name)
        logger.info('Signature:')
        logger.info(positives_signature)
        logger.info(negatives_signature)
        if positives_signature is None:
            logger.error('Could not understand channel names as defining a signature: %s',
                         positive_channel_names)
            self.request.sendall(''.encode('utf-8'))
            return
        if negatives_signature is None:
            logger.error(
                'Could not understand channel names as defining a signature: %s',
                negative_channel_names)
            self.request.sendall(''.encode('utf-8'))
            return
        logger.info('%s', f'{positives_signature:064b}')
        logger.info('%s', f'{negatives_signature:064b}')
        counts = self.server.counts_provider.count_structures_of_partial_signed_signature(
            positives_signature, negatives_signature, study_name)
        self.request.sendall(
            (json.dumps(counts) + self.get_end_of_transmission()).encode('utf-8'))

    def get_end_of_transmission(self):
        return chr(4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt countsserver start',
        description='Server providing counts of samples satisfying given partial signatures.',
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
        help='The directory in which this process will search for expression data binaries and '
        'the JSON index file.',
    )
    args = parser.parse_args()

    counts_provider = CountsProvider(args.source_data_location)
    tcp_server = socketserver.TCPServer(
        (args.host, args.port), CountsRequestHandler)
    tcp_server.counts_provider = counts_provider
    tcp_server.serve_forever(poll_interval=0.2)
