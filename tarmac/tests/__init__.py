# Copyright 2009 Paul Hummer
# This file is part of Tarmac.
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

'''Tests for Tarmac!'''
from cStringIO import StringIO
import os
import shutil
import unittest

from tarmac.config import TarmacConfig


class TarmacTestCase(unittest.TestCase):
    '''A base TestCase for all Tarmac tests.'''

    NEEDS_SAMPLE_DATA = False
    CONFIG_TEMPLATE = '''
[lp:~tarmac/tarmac/tarmac]
log_file = %(log_file)s
tree_dir = %(tree_dir)s

[lp:~tarmac/tarmac/tarmac2]
[lp:~tarmac/tarmac/tarmac3]
[lp:~tarmac/tarmac/tarmac4]
'''
    CREDS_TEMPLATE = '''
[1]
consumer_secret =
access_token = access
consumer_key = Tarmac
access_secret = secret
'''

    def setUp(self):

        # Set up the environment.
        self.tempdir = os.path.join(os.getcwd(), 'tmp')
        os.environ['TARMAC_CONFIG_HOME'] = os.path.join(
            self.tempdir, 'config')
        os.environ['TARMAC_CACHE_HOME'] = os.path.join(
            self.tempdir, 'cache')
        os.environ['TARMAC_PID_FILE'] = os.path.join(
            self.tempdir, 'pid-dir')
        os.environ['TARMAC_CREDENTIALS'] = os.path.join(
            self.tempdir, 'credentials')

        # Create self.tempdir; it is removed in tearDown().
        os.makedirs(self.tempdir)

        if self.NEEDS_SAMPLE_DATA:
            config = TarmacConfig()
            self.write_config_file(config)
            self.write_credentials_file(config)

    def tearDown(self):

        # Clean up environment.
        shutil.rmtree(self.tempdir)
        keys = ['TARMAC_CONFIG_HOME', 'TARMAC_CACHE_HOME', 'TARMAC_PID_FILE',
            'TARMAC_CREDENTIALS']
        for key in keys:
            try:
                del os.environ[key]
            except KeyError:
                pass

    def write_credentials_file(self, config=None):
        if not config:
            try:
                config = self.config
            except AttributeError:
                raise Exception('No config provided.')

        credentials = open(config.CREDENTIALS, 'ab')
        credentials.write(self.CREDS_TEMPLATE)
        credentials.close()

    def write_config_file(self, config=None):
        '''Parse the CONFIG_TEMPLATE without writing a file.'''
        if not config:
            try:
                config = self.config
            except AttributeError:
                raise Exception('No config provided.')

        template = self.CONFIG_TEMPLATE % {
            'log_file' : os.path.join(os.getcwd(),'tarmac.log'),
            'tree_dir' : os.path.join(os.getcwd(), 'trunk')
            }

        f = StringIO()
        f.write(template)
        f.reset()
        config.readfp(f)
        f.close()
