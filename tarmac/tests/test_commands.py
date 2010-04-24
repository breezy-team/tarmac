'''Tests for tarmac.bin.commands.py.'''
from cStringIO import StringIO
import os
import sys

from tarmac.bin import commands
from tarmac.config import TarmacConfig2
from tarmac.exceptions import CommandNotFound
from tarmac.tests import TarmacTestCase


class TestCommand(TarmacTestCase):
    '''Test for tarmac.bin.commands.Command.'''

    def test__init__(self):
        command_name = u'test'
        command = commands.TarmacCommand()
        command.NAME = command_name
        self.assertEqual(command.NAME, command_name)
        self.assertTrue(isinstance(command.config, TarmacConfig2))

    def test_run(self):
        command = commands.TarmacCommand()
        self.assertRaises(NotImplementedError, command.run)


class TestAuthCommand(TarmacTestCase):
    '''Test for tarmac.bin.command.cmd_auth.'''

    NEEDS_SAMPLE_DATA = True

    # XXX: rockstar - 10 Jan 2010 - How do I test this with the OAuth request,
    # etc?
    #def test_run(self):
    #    '''Test that calling the auth command gets a Lanuchpad token.'''

    #    tmp_stdout = StringIO()
    #    old_stdout = sys.stdout
    #    sys.stdout = tmp_stdout

    #    command = cmd_auth()
    #    self.assertFalse(os.path.exists(command.config.CREDENTIALS))
    #    command.run()
    #    self.assertEqual(tmp_stdout.getvalue(), '')

    #    sys.stdout = old_stdout

    def test_run_already_authenticated(self):
        '''If the user has already been authenticated, don't try again.'''
        tmp_stdout = StringIO()
        old_stdout = sys.stdout
        sys.stdout = tmp_stdout

        command = commands.cmd_auth()
        command.run()
        self.assertEqual(
            tmp_stdout.getvalue(),
            'You have already been authenticated.\n')

        sys.stdout = old_stdout


class TestHelpCommand(TarmacTestCase):

    def test_run(self):
        tmp_stdout = StringIO()
        old_stdout = sys.stdout
        sys.stdout = tmp_stdout

        command = commands.cmd_help()
        command.run()
        self.assertEqual(
            tmp_stdout.getvalue(),
            'You need help.\n')

        sys.stdout = old_stdout

class TestMergeCommand(TarmacTestCase):

    NEEDS_SAMPLE_DATA = True

    def test_run(self):
        tmp_stdout = StringIO()
        old_stdout = sys.stdout
        sys.stdout = tmp_stdout

        command = commands.cmd_merge()
        command.run()
        self.assertEqual(
            tmp_stdout.getvalue(),
            'Merging lp:~tarmac/tarmac/tarmac\n'
            'Merging lp:~tarmac/tarmac/tarmac3\n'
            'Merging lp:~tarmac/tarmac/tarmac2\n'
            'Merging lp:~tarmac/tarmac/tarmac4\n')

        sys.stdout = old_stdout
