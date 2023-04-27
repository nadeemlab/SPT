"""Entry point into the fast cell counts TCP server."""
import argparse
import json
import socketserver

from spatialprofilingtoolbox.countsserver.counts_provider import CountsProvider
from spatialprofilingtoolbox.countsserver.proximity_provider import ProximityProvider
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt countsserver start')


class CountsRequestHandler(socketserver.BaseRequestHandler):
    """The TCP server for fast cell counts."""
    def handle(self):
        data = self.request.recv(512).strip()
        logger.info('Request: %s', data)
        if self.handle_empty_body(data):
            return
        if self.handle_single_phenotype_counts_request(data):
            return
        if self.handle_proximity_request(data):
            return

    def handle_proximity_request(self, data):
        groups = self.get_groups(data)
        if len(groups) != 6:
            return False
        specification = self.get_phenotype_pair_specification(groups)
        study_name = specification[0]
        if self.handle_missing_study(study_name):
            return True

        try:
            metrics = self.get_proximity_metrics(*specification)
        except Exception as exception:
            message = "Error response."+ self.get_end_of_transmission()
            self.request.sendall(message.encode('utf-8'))
            raise exception

        message = json.dumps(metrics) + self.get_end_of_transmission()
        self.request.sendall(message.encode('utf-8'))
        return True

    def get_proximity_metrics(self, study, radius, positives1, negatives1, positives2, negatives2):
        phenotype1 = {'positive': positives1, 'negative': negatives1}
        phenotype2 = {'positive': positives2, 'negative': negatives2}
        return self.server.proximity_provider.compute_metrics(study, phenotype1, phenotype2, radius)

    def handle_single_phenotype_counts_request(self, data):
        groups = self.get_groups(data)
        if len(groups) != 3:
            return False
        specification = self.get_phenotype_spec(groups)
        study_name = specification[0]
        if self.handle_missing_study(study_name):
            return True

        positives_signature, negatives_signature = self.get_signatures(*specification)
        if self.handle_unparseable_signature(positives_signature, specification[1]):
            return True
        if self.handle_unparseable_signature(negatives_signature, specification[2]):
            return True

        counts = self.get_counts(study_name, positives_signature, negatives_signature)
        message = json.dumps(counts) + self.get_end_of_transmission()
        self.request.sendall(message.encode('utf-8'))
        return True

    def get_counts(self, study, positives_signature, negatives_signature):
        arguments = [positives_signature, negatives_signature, study]
        return self.server.counts_provider.count_structures_of_partial_signed_signature(*arguments)

    def handle_unparseable_signature(self, signature, names):
        if signature is None:
            logger.error('Could not understand channel names as defining a signature: %s', names)
            self.wrap_up_transmission()
            return True
        return False

    def get_signatures(self, study_name, positives, negatives):
        signature1 = self.server.counts_provider.compute_signature(positives, study_name)
        signature2 = self.server.counts_provider.compute_signature(negatives, study_name)
        logger.info('Signature: %s, %s', signature1, signature2)
        return signature1, signature2

    def handle_missing_study(self, study_name):
        if self.server.counts_provider.has_study(study_name):
            return False
        logger.error('Study not known to counts server: %s', study_name)
        self.wrap_up_transmission()
        return True

    def get_phenotype_spec(self, groups):
        record_separator = chr(30)
        study_name = groups[0]
        positive_channel_names = groups[1].split(record_separator)
        negative_channel_names = groups[2].split(record_separator)
        positive_channel_names = self.trim_empty_entry(positive_channel_names)
        negative_channel_names = self.trim_empty_entry(negative_channel_names)
        logger.info('Study: %s', study_name)
        logger.info('Positives: %s', positive_channel_names)
        logger.info('Negatives: %s', negative_channel_names)
        return study_name, positive_channel_names, negative_channel_names

    def get_phenotype_pair_specification(self, groups):
        record_separator = chr(30)
        study_name = groups[0]
        radius = int(groups[1])
        channel_lists = [
            self.trim_empty_entry(group.split(record_separator))
            for group in groups[2:6]
        ]
        return [study_name, radius, *channel_lists]

    def get_groups(self, data):
        group_separator = chr(29)
        return data.decode('utf-8').split(group_separator)

    def handle_empty_body(self, data):
        if data == '':
            logger.info('Empty body. Serving status.')
            status = json.dumps(self.server.counts_provider.get_status(), indent=4)
            message = status + self.get_end_of_transmission()
            self.request.sendall(message.encode('utf-8'))
            return True
        return False

    def wrap_up_transmission(self):
        self.request.sendall(self.get_end_of_transmission().encode('utf-8'))

    def get_end_of_transmission(self):
        return chr(4)

    def trim_empty_entry(self, element):
        if element == ['']:
            return []
        return element


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
    proximity_provider = ProximityProvider(args.source_data_location)
    tcp_server = socketserver.TCPServer((args.host, args.port), CountsRequestHandler)
    tcp_server.counts_provider = counts_provider
    tcp_server.proximity_provider = proximity_provider
    logger.info('countsserver is ready to accept connections.')
    tcp_server.serve_forever(poll_interval=0.2)
