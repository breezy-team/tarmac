'''Tests for tarmac.config'''
import os

from tarmac.config import TarmacConfig2
from tarmac.tests import TarmacTestCaseWithConfig

class TestTarmacConfig2(TarmacTestCaseWithConfig):
    '''Testing for tarmac.config.TarmacConfig2.'''

    CONFIG_TEMPLATE = '''
[lp:~tarmac/tarmac/tarmac]
log_file = /var/log/tarmac/tarmac.log
tree_dir = /var/cache/tarmac/tarmac

[lp:~tarmac/tarmac/tarmac2]
[lp:~tarmac/tarmac/tarmac3]
[lp:~tarmac/tarmac/tarmac4]
'''

    def test_CONFIG_HOME(self):
        '''Return the default CONFIG_HOME.'''
        del os.environ['TARMAC_CONFIG_HOME']
        config = TarmacConfig2()
        self.assertEqual(
            config.CONFIG_HOME,
            os.path.expanduser('~/.config/tarmac'))

    def test_CONFIG_HOME_environment(self):
        '''If TARMAC_CONFIG_HOME environment variable is set, use it.'''
        os.environ['TARMAC_CONFIG_HOME'] = '/'
        config = TarmacConfig2()
        self.assertEqual(config.CONFIG_HOME, '/')

    def test_CACHE_HOME(self):
        '''Return the default CACHE_HOME.'''
        del os.environ['TARMAC_CACHE_HOME']
        config = TarmacConfig2()
        self.assertEqual(
            config.CACHE_HOME,
            os.path.expanduser('~/.cache/tarmac'))

    def test_CACHE_HOME_environment(self):
        '''Return the environment set CACHE_HOME.'''
        os.environ['TARMAC_CACHE_HOME'] = '/'
        config = TarmacConfig2()
        self.assertEqual(config.CACHE_HOME, '/')

    def test_PID_FILE(self):
        '''Return the default path to the pid file.'''
        del os.environ['TARMAC_PID_FILE']
        config = TarmacConfig2()
        self.assertEqual(
            config.PID_FILE,
            os.path.join(config.CACHE_HOME, 'tarmac.pid'))

    def test_PID_FILE_environment(self):
        '''Return the environment set path to the pid file.'''
        os.environ['TARMAC_PID_FILE'] = '/tarmac.pid'
        config = TarmacConfig2()
        self.assertEqual(config.PID_FILE, '/tarmac.pid')

    def test_CREDENTIALS(self):
        '''Return the default path to credentials.'''
        del os.environ['TARMAC_CREDENTIALS']
        config = TarmacConfig2()
        self.assertEqual(
            config.CREDENTIALS,
            os.path.join(config.CONFIG_HOME, 'credentials'))

    def test_CREDENTIALS_environment(self):
        '''Return the environment set path to credentials.'''
        os.environ['TARMAC_CREDENTIALS'] = '/credentials'
        config = TarmacConfig2()
        self.assertEqual(
            config.CREDENTIALS,
            '/credentials')

    def test_CONFIG_FILE(self):
        '''Test that the config file is fetched properly.'''
        del os.environ['TARMAC_CONFIG_HOME']
        config = TarmacConfig2()
        self.assertTrue(
            config.CONFIG_FILE,
            os.path.join(
                os.path.expanduser('~/.config/tarmac'),
                'tarmac.conf'))

    def test_CONFIG_FILE_environment(self):
        '''Return the config file when the environment is changed.'''
        config = TarmacConfig2()
        self.assertTrue(
            config.CONFIG_FILE,
            os.path.join(
                self.tempdir,
                'config/tarmac.conf'))

    def test__check_config_dirs(self):
        '''Create the dirs required for configuration.'''
        config = TarmacConfig2()
        self.assertTrue(os.path.exists(config.CONFIG_HOME))
        self.assertTrue(os.path.exists(config.CACHE_HOME))

    def test_has_section(self):
        '''Ensure that the config is being read properly.'''
        config = TarmacConfig2()
        self.write_config_file(config)
        self.assertTrue(config.has_section('lp:~tarmac/tarmac/tarmac'))

    def test_get_sections(self):
        config = TarmacConfig2()
        self.write_config_file(config)
        self.assertEqual(len(config.branches), 4)

    def test_section_log_file(self):
        '''Ensure that the branch's log file can be read.'''
        config = TarmacConfig2()
        self.write_config_file(config)
        self.assertEqual(
            config.get('lp:~tarmac/tarmac/tarmac', 'log_file'),
            '/var/log/tarmac/tarmac.log')

    def test_section_log_file_NOT_SET(self):
        '''Get the default log file.'''
        config = TarmacConfig2()
        self.CONFIG_TEMPLATE = '''
[lp:~tarmac/tarmac/tarmac]
'''
        self.write_config_file(config)
        self.assertEqual(
            config.get('lp:~tarmac/tarmac/tarmac', 'log_file'),
            os.path.abspath('.'))

    def test_section_tree_dir(self):
        '''Ensure that the branch's tree cache can be read.'''
        config = TarmacConfig2()
        self.write_config_file(config)
        self.assertEqual(
            config.get('lp:~tarmac/tarmac/tarmac', 'tree_dir'),
            '/var/cache/tarmac/tarmac')

    def test_section_tree_dir_NOT_SET(self):
        '''Ensure that the branch's tree cache can be read.'''
        config = TarmacConfig2()
        self.CONFIG_TEMPLATE = '''
[lp:~tarmac/tarmac/tarmac]
'''
        self.write_config_file(config)
        self.assertEqual(
            config.get('lp:~tarmac/tarmac/tarmac', 'tree_dir'),
            '')
