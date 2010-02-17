'''Command options.'''
from bzrlib.option import Option


staging_option = Option(
    'staging', short_name='s',
    help=('Use staging as API source.'))
