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

from bzrlib.tests import TestCaseInTempDir
from tarmac.config import TarmacConfig


class TarmacTestCase(TestCaseInTempDir):
    '''A base TestCase for all Tarmac tests.'''

    CREDS_TEMPLATE = '''
[1]
consumer_secret =
access_token = access
consumer_key = Tarmac
access_secret = secret
'''

    def setUp(self):
        # Set up the environment.
        super(TarmacTestCase, self).setUp()

        self._oldtemp = tempfile.tempdir
        tempfile.tempdir = os.getcwd()
        self.tempdir = tempfile.mkdtemp(dir=os.getcwd())
        os.environ['TARMAC_CONFIG_HOME'] = os.path.join(
            self.tempdir, 'config')
        os.environ['TARMAC_CACHE_HOME'] = os.path.join(
            self.tempdir, 'cache')
        os.environ['TARMAC_PID_FILE'] = os.path.join(
            self.tempdir, 'pid-dir')
        os.environ['TARMAC_CREDENTIALS'] = os.path.join(
            self.tempdir, 'credentials')

        # Create the config for testing
        self.config = TarmacConfig()
        self.write_credentials_file()

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
        tempfile.tempdir = self._oldtemp
        super(TarmacTestCase, self).tearDown()

    def write_credentials_file(self):
        """Write out the temporary credentials file for testing."""
        credentials = open(self.config.CREDENTIALS, 'ab')
        credentials.write(self.CREDS_TEMPLATE)
        credentials.close()

    def add_branch_config(self, branch_path):
        """Add some fake config for a temporary local branch."""
        branch_url = 'file://%s' % branch_path
        if not branch_url in self.config.sections():
            self.config.add_section(branch_url)
        self.config.set(branch_url, 'tree_dir', branch_path)
        self.config.set(branch_url, 'log_file',
                        os.path.dirname(branch_path) + '.log')

    def remove_branch_config(self, branch_path):
        """Remove the config for the temporary local branch."""
        branch_url = 'file://%s' % os.path.dirname(branch_path)
        self.config.remove_section(branch_url)
