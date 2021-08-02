import logging
import re
import os
DEBUG = ('DEBUG' in os.environ)


class CustomFormatter(logging.Formatter):
    grey = '\x1b[38;21m'
    green = '\u001b[32m'
    bold_green = '\u001b[32;1m'
    magenta = '\u001b[35m'
    bold_magenta = '\u001b[35;1m'
    yellow = '\u001b[33m'
    bold_yellow = '\u001b[33;1m'
    red = '\u001b[31m'
    bold_red = '\u001b[31;1m'
    blue = '\u001b[34m'
    reset = '\u001b[0m'

    FORMATS = {
        logging.DEBUG: blue + '%(asctime)s ' + reset + magenta + '[  ' + reset + "%(levelname)s" + reset + magenta + '  ] ' + "%(name)s:" + reset + blue + "%(lineno)d" + magenta + ": " + reset + "%(message)s",
        logging.INFO: blue + '%(asctime)s ' + reset + magenta + '[  ' + reset + bold_green + "%(levelname)s" + reset + magenta + '   ] ' + "%(name)s: " + reset + "%(message)s",
        logging.WARNING: blue + '%(asctime)s ' + reset + magenta + '[ ' + reset + bold_yellow + "%(levelname)s" + reset + magenta + ' ] ' + "%(name)s:" + reset + blue + "%(lineno)d" + magenta + ": " + reset + "%(message)s",
        logging.ERROR: blue + '%(asctime)s ' + reset + magenta + '[  ' + reset + bold_red + "%(levelname)s" + reset + magenta + '  ] ' + "%(name)s:" + reset + blue + "%(lineno)d" + magenta + ": " + reset + "%(message)s",
        logging.CRITICAL: blue + '%(asctime)s ' + reset + magenta + '[ ' + reset + bold_red + "%(levelname)s" + reset + magenta + '] ' + "%(name)s:" + reset + blue + "%(lineno)d" + magenta + ": " + reset + "%(message)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%m-%d %H:%M:%S')
        return formatter.format(record)


def colorized_logger(name):
    """
    A lightweight customization of the Python standard library's ``logging`` module
    loggers, to provide colorized log messages.

    Args:
        name (str):
            The name of the logger to requisition. Typically a module's
            ``__name__`` attribute.

    Returns:
        The logger.
    """
    logger = logging.getLogger(re.sub('^spatialprofilingtoolbox\.', '', name))
    if DEBUG:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logger.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(CustomFormatter())
    logger.addHandler(ch)
    return logger
