
from ...standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)


def get_unique_value(dataframe, column):
    handles = sorted(list(set(dataframe[column]).difference([''])))
    if len(handles) == 0:
        message = 'No "%s" values are supplied for this run.' % column
        logger.error(message)
        raise ValueError(message)
    if len(handles) > 1:
        message = 'Multiple "%s" values were supplied for this run. Using "%s".' % (column, handles[0])
        logger.warning(message)
    return handles[0]
