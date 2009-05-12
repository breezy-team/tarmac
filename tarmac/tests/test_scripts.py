# Copyright 2009 Paul Hummer - See LICENSE
'''Tests for Tarmac scripts.'''
# pylint: disable-msg=W0212
__metaclass__ = type

from optparse import OptionParser
import sys
import unittest

from tarmac.bin import TarmacLander, TarmacScript


class TestTarmacScript(unittest.TestCase):
    '''Tests for tarmac.bin.TarmacScript.'''

    class TarmacDummyScript(TarmacScript):
        '''A dummy Tarmac script for testability.'''
        def _create_option_parser(self):
            return OptionParser()

    def test_create_option_parser_not_implemented(self):
        '''Test that the _create_config_parser method raises NotImplemented.'''
        self.assertRaises(NotImplementedError, TarmacScript, test_mode=True)

    def test_dummy_script_option_parser(self):
        '''Test that _create_config_parser is implemented in TarmacDummyScript.
        '''
        sys.argv = ['']
        script = self.TarmacDummyScript(test_mode=True)
        self.assertTrue(isinstance(script, self.TarmacDummyScript))


class TestTarmacLander(unittest.TestCase):
    '''Tests for TarmacLander.'''

    def test_lander_dry_run(self):
        '''Test that setting --dry-run sets the dry_run property.'''
        sys.argv = ['', 'foo', '--dry-run']
        script = TarmacLander(test_mode=True)
        self.assertTrue(script.dry_run)

    def test_lander_project(self):
        '''Test that the project argument gets handled properly.'''
        sys.argv = ['', 'foo']
        script = TarmacLander(test_mode=True)
        self.assertEqual(script.project, u'foo')

    def test_test_command(self):
        '''Test the --test-command option.'''
        sys.argv = ['', 'foo', '--test-command=trial foo.tests']
        script = TarmacLander(test_mode=True)
        self.assertEqual(script.test_command, u'trial foo.tests')

    def test_test_mode(self):
        '''Test that test_mode is set correctly.'''
        script = TarmacLander(test_mode=True)
        self.assertTrue(script.test_mode)
