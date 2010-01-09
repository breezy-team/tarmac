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
import os
import shutil
import tempfile
import unittest


class TarmacTestCase(unittest.TestCase):
    '''A base TestCase for all Tarmac tests.'''

    def setUp(self):

        # Set up the environment.
        self.tempdir = tempfile.mkdtemp()
        os.environ['TARMAC_CONFIG_HOME'] = os.path.join(
            self.tempdir, 'config')
        os.environ['TARMAC_CACHE_HOME'] = os.path.join(
            self.tempdir, 'cache')
        os.environ['TARMAC_PID_FILE'] = os.path.join(
            self.tempdir, 'pid-dir')
        os.environ['TARMAC_CREDENTIALS'] = os.path.join(
            self.tempdir, 'credentials')

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

    @property
    def CONFIG_TEMPLATE(self):
        raise NotImplementedError

    def write_credentials_file(self, config=None):
        if not config:
            try:
                config = self.config
            except AttributeError:
                raise Exception('No config provided.')

        credentials = open(config.CREDENTIALS, 'ab')
        credentials.write('')
        credentials.close()

    def write_config_file(self, config=None):
        '''Write out a fake config file for testing.'''
        if not config:
            try:
                config = self.config
            except AttributeError:
                raise Exception('No config provided.')

        assert not os.path.exists(config.CONFIG_FILE)
        f = open(config.CONFIG_FILE, 'ab')
        f.write(self.CONFIG_TEMPLATE)
        f.close()
        config.read(config.CONFIG_FILE)
