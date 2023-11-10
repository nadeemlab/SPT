"""Entry point into the fast cell counts TCP server."""

import argparse

from spatialprofilingtoolbox.db.database_connection import wait_for_database_ready
from spatialprofilingtoolbox.ondemand.fast_cache_assessor import FastCacheAssessor
from spatialprofilingtoolbox.ondemand.tcp_server import (
    OnDemandTCPServer,
    OnDemandProviderSet,
)
from spatialprofilingtoolbox.ondemand.providers.counts_provider import CountsProvider
from spatialprofilingtoolbox.ondemand.providers.proximity_provider import ProximityProvider
from spatialprofilingtoolbox.ondemand.providers.squidpy_provider import SquidpyProvider

from spatialprofilingtoolbox.ondemand.request_handler import OnDemandRequestHandler
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt ondemand start')


def start() -> None:
    source_data_location, host, port, service, timeout = get_cli_arguments()
    setup_data_sources(source_data_location, service)
    start_services(source_data_location, host, port, service, timeout)


def setup_data_sources(source_data_location: str, service: str | None) -> None:
    wait_for_database_ready()
    assessor = FastCacheAssessor(source_data_location)
    if service is None or service == CountsProvider.service_specifier():
        assessor.assess_and_act()
    else:
        assessor.block_until_available()


def start_services(
    source_data_location: str,
    host: str,
    port: int,
    service: str | None, 
    timeout: int,
) -> None:
    service_classes = (CountsProvider, ProximityProvider, SquidpyProvider)
    specifiers_classes = {c.service_specifier(): c for c in service_classes}
    providers_initialized = {
        specifier: service_class(source_data_location, timeout) if service in (specifier, None) else None
        for specifier, service_class in specifiers_classes.items()
    }
    tcp_server = OnDemandTCPServer(
        (host, port),
        OnDemandRequestHandler,
        OnDemandProviderSet(**providers_initialized), # type: ignore
    )
    if service is not None:
        logger.info('Service "%s" is ready to accept connections.', service)
    else:
        logger.info('Ondemand services are ready to accept connections.')
    tcp_server.serve_forever(poll_interval=0.2)


def get_cli_arguments() -> tuple[str, str, int, str | None, int]:
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
        '--timeout-seconds',
        dest='timeout_seconds',
        type=int,
        default=300,
        help='Maximum runtime that will be tolerated by a single feature value computation, after '
        'which a null is presumed. Default 300 (seconds).'
    )
    service_classes = [CountsProvider, ProximityProvider, SquidpyProvider]
    parser.add_argument(
        '--service',
        dest='service',
        choices=tuple(c.service_specifier() for c in service_classes),
        type=str,
        default=None,
        help='Choose which service to start. If not provided, all services will be started.',
    )
    args = parser.parse_args()
    return args.source_data_location, args.host, args.port, args.service, args.timeout_seconds


if __name__ == '__main__':
    start()
