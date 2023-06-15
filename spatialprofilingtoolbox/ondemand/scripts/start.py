"""Entry point into the fast cell counts TCP server."""
import socketserver
import argparse

from spatialprofilingtoolbox.apiserver.app.db_accessor import DBAccessor
from spatialprofilingtoolbox.ondemand.fast_cache_assessor import FastCacheAssessor
from spatialprofilingtoolbox.ondemand.counts_provider import CountsProvider
from spatialprofilingtoolbox.ondemand.proximity_provider import ProximityProvider
from spatialprofilingtoolbox.ondemand.counts_request_handler import CountsRequestHandler
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt ondemand start')

def start():
    source_data_location, host, port = get_cli_arguments()
    setup_data_sources(source_data_location)
    start_services(source_data_location, host, port)

def setup_data_sources(source_data_location):
    DBAccessor.wait_for_database_ready()
    assessor = FastCacheAssessor(source_data_location)
    assessor.assess()

def start_services(source_data_location, host, port):
    counts_provider = CountsProvider(source_data_location)
    proximity_provider = ProximityProvider(source_data_location)
    tcp_server = socketserver.TCPServer((host, port), CountsRequestHandler)
    tcp_server.counts_provider = counts_provider
    tcp_server.proximity_provider = proximity_provider
    logger.info('ondemand is ready to accept connections.')
    tcp_server.serve_forever(poll_interval=0.2)

def get_cli_arguments():
    parser = argparse.ArgumentParser(
        prog='spt ondemand start',
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
        default='/ondemand/source_data/',
        help='The directory in which this process will search for expression data binaries and '
        'the JSON index file. If they are not found, this program will attempt to create them '
        'from data in the database referenced by argument DATABASE_CONFIG_FILE.',
    )
    args = parser.parse_args()
    return args.source_data_location, args.host, args.port

if __name__ == '__main__':
    start()
