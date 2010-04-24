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

from tarmac.tests import TarmacTestCase


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
        self.assertEqual(output, 'You need help.')

    def test_script_merge(self):
        status, output = self.exec_tarmac_script('merge')
        self.assertEqual(
            output,
            'Merging lp:~tarmac/tarmac/tarmac\n'
            'Merging lp:~tarmac/tarmac/tarmac3\n'
            'Merging lp:~tarmac/tarmac/tarmac2\n'
            'Merging lp:~tarmac/tarmac/tarmac4')
