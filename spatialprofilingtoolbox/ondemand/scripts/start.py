"""Entry point into the computation worker service."""

from spatialprofilingtoolbox.db.database_connection import wait_for_database_ready

from spatialprofilingtoolbox.ondemand.worker import OnDemandWorker
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt ondemand start')


if __name__ == '__main__':
    wait_for_database_ready()
    worker = OnDemandWorker()
    logger.info('Starting on-demand computations worker.')
    worker.start()
