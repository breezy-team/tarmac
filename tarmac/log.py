'''Logging utilities for Tarmac.'''
import errno
import logging
import os
import sys

from tarmac.config import TarmacConfig


def ensure_log_dir(log_file):
    if not log_file:
        return
    log_dir = os.path.dirname(log_file)
    try:
        os.makedirs(log_dir)
    except OSError, e:
        # If the directory already exists, just pass. Otherwise, log to stderr
        # because we probably can't write to the actual log file.
        if getattr(e, 'errno', None) != errno.EEXIST:
            err_msg = "Failed to create logging directory: %s\n%s\n" % (
                log_dir, str(e))
            sys.stderr.write(err_msg)


def set_up_logging(config=None):
    if not config:
        config = TarmacConfig()

    # Set up logging.
    logger = logging.getLogger('tarmac')
    logger.setLevel(logging.DEBUG)

    log_file = config.get('Tarmac', 'log_file')
    ensure_log_dir(log_file)
    file_handler = logging.FileHandler(filename=log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s %(levelname)-8s %(message)s',
                          '%Y-%m-%d %H:%M:%S'))
    logger.addHandler(file_handler)
    logger.debug('Logging to %(logfile)s' % {'logfile': log_file})

    # Handle logging for 'bzr' logger
    bzr_logger = logging.getLogger('bzr')
    bzr_logger.setLevel(logging.INFO)
    bzr_logger.addHandler(file_handler)


def set_up_debug_logging():
    logger = logging.getLogger('tarmac')
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.DEBUG)
    logger.addHandler(stderr_handler)
