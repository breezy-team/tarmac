'''Logging utilities for Tarmac.'''
import logging
import sys

from tarmac.config import TarmacConfig


def set_up_logging():
    config = TarmacConfig()

    # Set up logging.
    logger = logging.getLogger('tarmac')
    logger.setLevel(logging.DEBUG)

    log_file = config.get('Tarmac', 'log_file')
    file_handler = logging.FileHandler(filename=log_file)
    file_handler.setLevel(logging.WARN)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s %(levelname)-8s %(message)s',
                          '%Y-%m-%d %H:%M:%S'))
    logger.addHandler(file_handler)
    logger.debug('Logging to %(logfile)s' % {'logfile': log_file})

def set_up_debug_logging():
    logger = logging.getLogger('tarmac')
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.DEBUG)
    logger.addHandler(stderr_handler)
