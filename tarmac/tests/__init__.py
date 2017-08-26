# Copyright 2009 Paul Hummer
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
import math
import os
import shutil
import tempfile

from base64 import b64encode
from breezy.controldir import ControlDir
from breezy.directory_service import directories
from breezy.tests import TestCaseInTempDir
from breezy.transport import register_urlparse_netloc_protocol

from tarmac import branch
from tarmac.bin.commands import TarmacCommand
from tarmac.config import TarmacConfig


class MockLPProject(object):
    '''A mock LP Project.'''

    def __init__(self):
        self.name = b64encode(
            os.urandom(int(math.ceil(0.75 * 10))), '-_')[:10]


class MockLPBranch(object):
    '''A mock LP Branch.'''

    def __init__(self, tree_dir, source_branch=None):
        self.tree_dir = tree_dir
        os.makedirs(tree_dir)
        if source_branch:
            source_dir = source_branch._internal_bzr_branch.controldir
            controldir = source_dir.sprout(tree_dir)
            self._internal_tree, self._internal_bzr_branch = \
                    controldir.open_tree_or_branch(tree_dir)
            self.revision_count = source_branch.revision_count
        else:
            self._internal_bzr_branch = ControlDir.create_branch_convenience(
                tree_dir)
            self.revision_count = 0
        self.bzr_identity = 'lp:%s' % os.path.basename(self.tree_dir)
        self.web_link = self.bzr_identity
        self.unique_name = self.bzr_identity
        self.project = MockLPProject()


class cmd_mock(TarmacCommand):
    '''A mock command.'''

    def run(self):
        """Just a dummy command that does nothing."""


class MockModule(object):
    """A mock module."""

    def __init__(self):
        self.__dict__['cmd_mock'] = cmd_mock


class Thing(dict):
    """Quickly create an object with given attributes."""

    def __init__(self, **names):
        super(Thing, self).__init__(self, **names)
        self.__dict__.update(names)

    def __iter__(self):
        for item in self.values():
            if not callable(item):
                yield item


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
        if branch_path.endswith('/'):
            branch_url = 'lp:%s' % os.path.dirname(branch_path)[-2]
        else:
            branch_url = 'lp:%s' % os.path.basename(branch_path)
        if not branch_url in self.config.sections():
            self.config.add_section(branch_url)
        self.config.set(branch_url, 'tree_dir', branch_path)
        self.config.set(branch_url, 'log_file',
                        os.path.dirname(branch_path) + '.log')

    def remove_branch_config(self, branch_path):
        """Remove the config for the temporary local branch."""
        if branch_path.endswith('/'):
            branch_url = 'lp:%s' % os.path.dirname(branch_path)[-2]
        else:
            branch_url = 'lp:%s' % os.path.basename(branch_path)
        self.config.remove_section(branch_url)


class TarmacDirectoryFactory(object):
    def __init__(self, path):
        self.path = path

    def __call__(self):
        return self

    def look_up(self, name, url):
        real = 'file://%(path)s/%(name)s' % {'path': self.path,
                                             'name': name}
        return real


class BranchTestCase(TarmacTestCase):
    """Test case for tests which need to use branches."""

    def setUp(self):
        """Set up the test environment."""
        super(BranchTestCase, self).setUp()

        register_urlparse_netloc_protocol('lp')
        directories.register('lp:',
                             TarmacDirectoryFactory(self.TEST_ROOT),
                             'Fake factory for lp: urls',
                             override_existing=True)

        self.branch1, self.branch2 = self.make_two_branches_to_merge()

    def tearDown(self):
        """Tear down the tests."""
        self.remove_branch_config(self.branch1.lp_branch.bzr_identity)
        self.remove_branch_config(self.branch2.lp_branch.bzr_identity)
        shutil.rmtree(self.branch1.lp_branch.tree_dir)
        shutil.rmtree(self.branch2.lp_branch.tree_dir)

        super(BranchTestCase, self).tearDown()

    def make_two_branches_to_merge(self):
        """Make two branches, one with revisions to merge."""
        branch1_dir = os.path.join(self.TEST_ROOT, 'branch1')
        branch2_dir = os.path.join(self.TEST_ROOT, 'branch2')
        self.add_branch_config(branch1_dir)
        self.add_branch_config(branch2_dir)

        mock1 = MockLPBranch(branch1_dir)
        branch1 = branch.Branch.create(mock1, self.config, create_tree=True)
        branch1.commit("Reading, 'riting, 'rithmetic")
        branch1.lp_branch.revision_count += 1

        mock2 = MockLPBranch(branch2_dir, source_branch=branch1.lp_branch)
        branch2 = branch.Branch.create(mock2, self.config, create_tree=True,
                                       target=branch1)
        branch2.commit('ABC...')

        added_file = os.path.join(branch2.lp_branch.tree_dir, 'README')
        with open(added_file, 'w+') as f:
            f.write('This is a test file.')
            f.close()
        branch2.tree.add(['README'])
        branch2.commit('Added a README for testing')
        branch2.lp_branch.revision_count += 2

        return branch1, branch2
