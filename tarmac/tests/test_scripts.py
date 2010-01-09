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

'''Tests for Tarmac scripts.'''
# pylint: disable-msg=W0212,W0223
__metaclass__ = type

import commands
from optparse import OptionParser
import sys

from tarmac.bin import TarmacLander, TarmacScript
from tarmac.tests import TarmacTestCase


class TestTarmacScript(TarmacTestCase):
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


class TestTarmacLander(TarmacTestCase):
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

    def test_test_mode(self):
        '''Test that test_mode is set correctly.'''
        script = TarmacLander(test_mode=True)
        self.assertTrue(script.test_mode)


class TestTarmacScript(TarmacTestCase):
    '''Tests for tarmac-script.'''

    NEEDS_SAMPLE_DATA = True

    def exec_tarmac_script(self, args):
        '''Execute the file tarmac-script with the provided arguments.'''
        return commands.getstatusoutput('../tarmac-script %(args)s' % {
            'args': args})

    def test_script(self):
        status, output = self.exec_tarmac_script('')
        self.assertEqual(output, 'You need help.')

    # XXX: rockstar - 10 Jan 2010 - How do I test this with the OAuth request,
    # etc?
    #def test_script_auth(self):
    #    status, output = self.exec_tarmac_script('auth')
    #    self.assertEqual(output, 'authenticated')

    def test_script_help(self):
        status, output = self.exec_tarmac_script('help')
        status, output = commands.getstatusoutput('../tarmac-script help')
        self.assertEqual(output, 'You need help.')

    def test_script_merge(self):
        status, output = self.exec_tarmac_script('merge')
        self.assertEqual(
            output,
            'Merging lp:~tarmac/tarmac/tarmac\n'
            'Merging lp:~tarmac/tarmac/tarmac3\n'
            'Merging lp:~tarmac/tarmac/tarmac2\n'
            'Merging lp:~tarmac/tarmac/tarmac4')
