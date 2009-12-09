'''Tests for tarmac.config'''
import os
import shutil
import tempfile
import unittest

from tarmac.config import TarmacConfig2

class TestTarmacConfig2(unittest.TestCase):
    '''Testing for tarmac.config.TarmacConfig2.'''

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

    def create_fake_config(self, config):
        '''Write out a fake config file for testing.'''
        assert not os.path.exists(config.CONFIG_FILE)
        f = open(config.CONFIG_FILE, 'ab')
        f.write(''.join([
            '[lp:~tarmac/tarmac/tarmac]\n',
            '']))
        f.close()
        config.read(config.CONFIG_FILE)

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
        self.create_fake_config(config)
        self.assertTrue(config.has_section('lp:~tarmac/tarmac/tarmac'))
