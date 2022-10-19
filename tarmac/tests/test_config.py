'''Tests for tarmac.config'''
import os

from configparser import NoOptionError
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
        branch_url = 'lp:%s' % os.path.basename(tree_dir)
        self.add_branch_config(tree_dir)
        self.assertEqual(self.config.get(branch_url, 'tree_dir'),
                         tree_dir)
        self.remove_branch_config(tree_dir)

    def test_section_tree_dir_NOT_SET(self):
        '''Ensure that the branch's tree cache can be read.'''
        config = BranchConfig('lp:test_no_tree_dir', self.config)
        self.assertIs(None, config.tree_dir)

    def test_set(self):
        """Test that the set override method works properly."""
        self.config.set('Tarmac', 'test_value', 'testing')
        self.assertEqual(self.config.get('Tarmac', 'test_value'),
                         self.config.test_value)
        self.config.add_section('test')
        self.config.set('test', 'test_option', 'foo')
        self.assertFalse(hasattr(self.config, 'test_option'))
        self.config.remove_section('test')

    def test_remove_option(self):
        """Test that the remove_option wrapper method works properly."""
        self.config.set('Tarmac', 'test_value', 'testing')
        self.assertTrue(hasattr(self.config, 'test_value'))
        self.config.remove_option('Tarmac', 'test_value')
        self.assertFalse(hasattr(self.config, 'test_value'))
        self.config.add_section('test')
        self.config.set('test', 'test_option', 'foo')
        self.assertFalse(hasattr(self.config, 'test_option'))
        self.config.remove_option('test', 'test_option')
        self.assertRaises(NoOptionError,
                          self.config.get, 'test', 'test_option')
        self.config.remove_section('test')


class BranchConfigTestCase(TarmacTestCase):
    '''Tests for the tarmac.config.BranchConfig object.'''

    def test_get_value(self):
        expected_value = 'test value'
        self.config.add_section('lp:test_get_value')
        self.config.set('lp:test_get_value', 'test_key', expected_value)

        config = BranchConfig('lp:test_get_value', self.config)

        self.assertTrue(config.get('test_key'))
        self.assertEqual(config.get('test_key'), expected_value)

    def test_get_unset_value_returns_none(self):
        config = BranchConfig('lp:test_no_keys', self.config)
        self.assertFalse(hasattr(config, 'missing_key'))
        self.assertIs(None, config.get('missing_key'))
