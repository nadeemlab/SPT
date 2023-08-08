"""Entry point into the fast cell counts TCP server."""

import argparse

from spatialprofilingtoolbox.db.database_connection import wait_for_database_ready
from spatialprofilingtoolbox.ondemand.fast_cache_assessor import FastCacheAssessor
from spatialprofilingtoolbox.ondemand.tcp_server import (
    OnDemandTCPServer,
    OnDemandProviderSet,
)
from spatialprofilingtoolbox.ondemand.providers import (
    CountsProvider,
    ProximityProvider,
    SquidpyProvider,
)
from spatialprofilingtoolbox.ondemand.request_handler import OnDemandRequestHandler
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt ondemand start')


def start():
    source_data_location, host, port = get_cli_arguments()
    setup_data_sources(source_data_location)
    start_services(source_data_location, host, port)


def setup_data_sources(source_data_location):
    wait_for_database_ready()
    assessor = FastCacheAssessor(source_data_location)
    assessor.assess_and_act()


def start_services(source_data_location: str, host: str, port: int) -> None:
    counts = CountsProvider(source_data_location)
    proximity = ProximityProvider(source_data_location)
    squidpy = SquidpyProvider(source_data_location)
    tcp_server = OnDemandTCPServer(
        (host, port),
        OnDemandRequestHandler,
        OnDemandProviderSet(counts = counts, proximity = proximity, squidpy = squidpy),
    )
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
