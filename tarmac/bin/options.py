# Copyright 2010-2011 Paul Hummer
# Copyright 2010-2014 Canonical Ltd.
#
# Tarmac is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by
# the Free Software Foundation.
#
# Tarmac is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tarmac.  If not, see <http://www.gnu.org/licenses/>.
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
imply_commit_message_option = Option(
    'imply-commit-message',
    help=("Use the description as a commit message if the branch "
          "doesn't have a message"))
one_option = Option(
    'one', short_name='1',
    help='Merge only one branch and exit.')
list_approved_option = Option(
    'list-approved', short_name='l',
    help='List Approved merge proposals for the target branch.')
