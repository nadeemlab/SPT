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

COUNTS = 'counts'
PROXIMITY = 'proximity'
SQUIDPY = 'squidpy'


def start() -> None:
    source_data_location, host, port, service = get_cli_arguments()
    setup_data_sources(source_data_location)
    start_services(source_data_location, host, port, service)


def setup_data_sources(source_data_location: str) -> None:
    wait_for_database_ready()
    assessor = FastCacheAssessor(source_data_location)
    assessor.assess_and_act()


def start_services(source_data_location: str, host: str, port: int, service: str | None) -> None:
    counts = CountsProvider(source_data_location) if (service in {'counts', None}) else None
    proximity = ProximityProvider(source_data_location) if (service in {'proximity', None}) else \
        None
    squidpy = SquidpyProvider(source_data_location) if (service in {'squidpy', None}) else None
    tcp_server = OnDemandTCPServer(
        (host, port),
        OnDemandRequestHandler,
        OnDemandProviderSet(counts=counts, proximity=proximity, squidpy=squidpy),
    )
    if service is not None:
        logger.info('Service "%s" is ready to accept connections.', service)
    else:
        logger.info('Ondemand services are ready to accept connections.')
    tcp_server.serve_forever(poll_interval=0.2)


def get_cli_arguments() -> tuple[str, str, int, str | None]:
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
    parser.add_argument(
        '--service',
        dest='service',
        choices=(COUNTS, PROXIMITY, SQUIDPY),
        type=str,
        default=None,
        help='Choose which service to start. If not provided, all services will be started.',
    )
    args = parser.parse_args()
    return args.source_data_location, args.host, args.port, args.service


if __name__ == '__main__':
    start()
