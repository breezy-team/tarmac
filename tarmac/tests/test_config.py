'''Tests for tarmac.config'''
import os
import unittest

from tarmac.config import TarmacConfig2

class TestTarmacConfig2(unittest.TestCase):
    '''Testing for tarmac.config.TarmacConfig2.'''

    def test_CONFIG_HOME(self):
        config = TarmacConfig2()
        self.assertEqual(
            config.CONFIG_HOME,
            os.path.expanduser('~/.config/tarmac'))

    def test_CONFIG_HOME_environment(self):
        os.environ['TARMAC_CONFIG_HOME'] = '/'
        config = TarmacConfig2()
        self.assertEqual(
            config.CONFIG_HOME,
            '/')
