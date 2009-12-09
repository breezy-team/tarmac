'''Tests for tarmac.config'''
import os
import tempfile
import unittest

from tarmac.config import TarmacConfig2

class TestTarmacConfig2(unittest.TestCase):
    '''Testing for tarmac.config.TarmacConfig2.'''

    def _create_test_config_environment(self):
        tempdir = tempfile.mkdtemp()
        os.environ['TARMAC_CONFIG_HOME'] = os.path.join(
            tempdir, 'config')
        os.environ['TARMAC_CACHE_HOME'] = os.path.join(
            tempdir, 'cache')
        os.environ['TARMAC_PID_FILE'] = os.path.join(
            tempdir, 'pid-dir')
        os.environ['TARMAC_CREDENTIALS'] = os.path.join(
            tempdir, 'credentials')
        return tempdir

    def test_CONFIG_HOME(self):
        '''Return the default CONFIG_HOME.'''
        config = TarmacConfig2()
        self.assertEqual(
            config.CONFIG_HOME,
            os.path.expanduser('~/.config/tarmac'))

    def test_CONFIG_HOME_environment(self):
        '''If TARMAC_CONFIG_HOME environment variable is set, use it.'''
        os.environ['TARMAC_CONFIG_HOME'] = '/'
        config = TarmacConfig2()
        self.assertEqual(config.CONFIG_HOME, '/')
        del os.environ['TARMAC_CONFIG_HOME']

    def test_CACHE_HOME(self):
        '''Return the default CACHE_HOME.'''
        config = TarmacConfig2()
        self.assertEqual(
            config.CACHE_HOME,
            os.path.expanduser('~/.cache/tarmac'))

    def test_CACHE_HOME_environment(self):
        '''Return the environment set CACHE_HOME.'''
        os.environ['TARMAC_CACHE_HOME'] = '/'
        config = TarmacConfig2()
        self.assertEqual(config.CACHE_HOME, '/')
        del os.environ['TARMAC_CACHE_HOME']

    def test_PID_FILE(self):
        '''Return the default path to the pid file.'''
        config = TarmacConfig2()
        self.assertEqual(
            config.PID_FILE,
            os.path.join(config.CACHE_HOME, 'tarmac.pid'))

    def test_PID_FILE_environment(self):
        '''Return the environment set path to the pid file.'''
        os.environ['TARMAC_PID_FILE'] = '/tarmac.pid'
        config = TarmacConfig2()
        self.assertEqual(config.PID_FILE, '/tarmac.pid')
        del os.environ['TARMAC_PID_FILE']

    def test_CREDENTIALS(self):
        '''Return the default path to credentials.'''
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
        del os.environ['TARMAC_CREDENTIALS']

    def test__check_config_dirs(self):
        '''Create the dirs required for configuration.'''
        tempdir = self._create_test_config_environment()
        config = TarmacConfig2()
        self.assertTrue(os.path.exists(
            os.path.join(tempdir, 'config')))
        self.assertTrue(os.path.exists(
            os.path.join(tempdir, 'cache')))
