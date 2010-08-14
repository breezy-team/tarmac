'''Tests for tarmac.config'''
import os

from tarmac.config import BranchConfig
from tarmac.tests import TarmacTestCase


class TestTarmacConfig(TarmacTestCase):
    '''Testing for tarmac.config.TarmacConfig.'''

    def test_check_config_dirs(self):
        '''Create the dirs required for configuration.'''
        self.assertTrue(os.path.exists(self.config.CONFIG_HOME))
        self.assertTrue(os.path.exists(self.config.CACHE_HOME))

    def test_section_log_file(self):
        '''Ensure that the branch's log file can be read.'''
        log_file = os.path.join(self.config.CONFIG_HOME, 'tarmac.log')
        self.assertEqual(self.config.get('Tarmac', 'log_file'), log_file)

    def test_section_log_file_NOT_SET(self):
        '''Get the default log file.'''
        config = BranchConfig('lp:test_no_log_file', self.config)
        self.assertFalse(hasattr(config, 'log_file'))

    def test_section_tree_dir(self):
        '''Ensure that the branch's tree cache can be read.'''
        tree_dir = os.path.join(self.tempdir, 'trunk')
        self.add_branch_config(tree_dir)
        self.assertEqual(self.config.get('file://%s' % tree_dir,'tree_dir'),
                         tree_dir)
        self.remove_branch_config(tree_dir)

    def test_section_tree_dir_NOT_SET(self):
        '''Ensure that the branch's tree cache can be read.'''
        config = BranchConfig('lp:test_no_tree_dir', self.config)
        self.assertFalse(hasattr(config, 'tree_dir'))
