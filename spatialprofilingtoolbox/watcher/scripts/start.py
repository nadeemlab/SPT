"""Start the service to watch the computation worker activity and response to some events."""

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

from spatialprofilingtoolbox.db.database_connection import wait_for_database_ready

from spatialprofilingtoolbox.watcher.watcher import WorkerWatcher
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt watcher start')


if __name__ == '__main__':
    parser = ArgumentParser(
        prog='spt watcher start',
        description='Watch computation workers for possible failures.',
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.parse_args()
    wait_for_database_ready()
    watcher = WorkerWatcher()
    logger.info('Starting worker watcher.')
    watcher.start()
