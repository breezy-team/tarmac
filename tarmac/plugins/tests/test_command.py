# Copyright 2010 Canonical, Ltd.
#
# This file is part of Tarmac.
#
# Tarmac is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# Tarmac is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tarmac.  If not, see <http://www.gnu.org/licenses/>.
"""Tests for the Command plug-in."""

import os

from tarmac.bin.registry import CommandRegistry
from tarmac.plugins import command
from tarmac.tests import TarmacTestCase
from tarmac.tests.test_commands import FakeCommand
from tarmac.tests.mock import Thing


class TestCommand(TarmacTestCase):
    """Test the Command plug-in."""

    def setUp(self):
        """Set up additional data we need for all tests."""
        super(TestCommand, self).setUp()
        self.proposal = Thing(
            source_branch=Thing(
                display_name='lp:project/source'),
            target_branch=Thing(
                display_name='lp:project'))
        self.plugin = command.Command()
        registry = CommandRegistry(config=self.config)
        self.command = FakeCommand(registry)

    def test_run(self):
        """Test that the plug-in runs without errors."""
        target = Thing(config=Thing(
                verify_command="/bin/true"),
                       tree=Thing(abspath=os.path.abspath))
        self.plugin.run(
            command=self.command, target=target, source=None,
            proposal=self.proposal)

    def test_run_failure(self):
        """Test that a failure raises the correct exception."""
        target = Thing(config=Thing(
                verify_command="/bin/false"),
                       tree=Thing(abspath=os.path.abspath))
        self.assertRaises(command.VerifyCommandFailed,
                          self.plugin.run,
                          command=self.command, target=target, source=None,
                          proposal=self.proposal)

    def test_run_nonascii_failure(self):
        self.config.debug = False
        target = Thing(config=Thing(
                verify_command="python -c 'import sys;"
                           " sys.stdout.write(\"f\\xc3\\xa5\\xc3\\xafl\"\n);"
                           " sys.exit(1)'"),
            tree=Thing(abspath=os.path.abspath))
        e = self.assertRaises(command.VerifyCommandFailed,
                              self.plugin.run,
                              command=self.command, target=target, source=None,
                              proposal=self.proposal)
        self.assertEqual(u'The attempt to merge lp:project/source'
                         u' into lp:project failed.'
                         u' Below is the output from the failed tests.'
                         u'\n\nf\xe5\xefl\n',
                         e.comment)
