# Copyright 2010-2013 Canonical, Ltd.
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

from unittest.mock import patch
from tarmac.bin.registry import CommandRegistry
from tarmac.plugins import command
from tarmac.tests import TarmacTestCase
from tarmac.tests.test_commands import FakeCommand
from tarmac.tests import Thing


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

    @patch('tarmac.plugins.command.export')
    def test_run(self, mocked):
        """Test that the plug-in runs without errors."""
        target = Thing(config=Thing(
                verify_command="/bin/true"),
                       tree=Thing(abspath=os.path.abspath))
        self.plugin.run(
            command=self.command, target=target, source=None,
            proposal=self.proposal)

    @patch('tarmac.plugins.command.export')
    def test_run_failure(self, mocked):
        """Test that a failure raises the correct exception."""
        target = Thing(config=Thing(
                verify_command="/bin/false"),
                       tree=Thing(abspath=os.path.abspath))
        self.assertRaises(command.VerifyCommandFailed,
                          self.plugin.run,
                          command=self.command, target=target, source=None,
                          proposal=self.proposal)

    @patch('tarmac.plugins.command.export')
    def test_run_exported_tree(self, mocked):
        """Test that the plug-in runs the command in an exported tree."""
        target = Thing(config=Thing(
                verify_command="/bin/true"),
                       tree=Thing(abspath=os.path.abspath))
        self.plugin.run(
            command=self.command, target=target, source=None,
            proposal=self.proposal)
        self.assertTrue(mocked.called_args_list[1].startswith(
            '/tmp/tarmac/branch.'))

    @patch('tarmac.plugins.command.export')
    def test_run_nonascii_failure(self, mocked):
        """Test that we avoid a UnicodeDecodeError from stdout/stderr.

        We need to create a bit of an odd string here that gets written
        to the stdout for the command, and check that we didn't get the
        UnicodeDecodeError raised. See bug #750930 for more.
        """
        self.config.debug = False
        target = Thing(config=Thing(
            verify_command=(
                "python -c 'import sys;"
                " sys.stdout.write(\"f\xe5\xefl\");"
                " sys.exit(1)'")),
            tree=Thing(abspath=os.path.abspath))
        e = self.assertRaises(command.VerifyCommandFailed,
                              self.plugin.run,
                              command=self.command, target=target, source=None,
                              proposal=self.proposal)
        self.assertEqual('The attempt to merge lp:project/source'
                         ' into lp:project failed.'
                         ' Below is the output from the failed tests.'
                         '\n\nf\xe5\xefl\n',
                         e.comment)
