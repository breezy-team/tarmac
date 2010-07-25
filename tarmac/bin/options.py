'''Command options.'''
from bzrlib.option import Option


debug_option = Option(
    'debug', short_name='d',
    help='Set loglevel to DEBUGGING and log to standard out.')
http_debug_option = Option(
    'http-debug',
    help='Debug launchpadlib calls to the webservice.')
staging_option = Option(
    'staging', short_name='s',
    help='Use staging as API source.')
