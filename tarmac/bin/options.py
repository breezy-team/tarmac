'''Command options.'''
from bzrlib.option import Option


debug_option = Option(
    'debug', short_name='d',
    help='Set loglevel to DEBUGGING and log to standard out.')
staging_option = Option(
    'staging', short_name='s',
    help='Use staging as API source.')
