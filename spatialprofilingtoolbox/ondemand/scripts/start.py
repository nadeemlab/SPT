"""Entry point into the computation worker service."""

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

from spatialprofilingtoolbox.db.database_connection import wait_for_database_ready

from spatialprofilingtoolbox.ondemand.worker import OnDemandWorker
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt ondemand start')


if __name__ == '__main__':
    parser = ArgumentParser(
        prog='spt ondemand start',
        description='Start a worker to do computation jobs.',
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.parse_args()
    wait_for_database_ready()
    worker = OnDemandWorker()
    logger.info('Starting on-demand computations worker.')
    worker.start()
