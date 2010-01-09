'''Tests for tarmac.bin2.commands.py.'''
from cStringIO import StringIO
import os
import sys

from tarmac.bin2 import commands
from tarmac.config import TarmacConfig2
from tarmac.exceptions import CommandNotFound
from tarmac.tests import TarmacTestCase


class TestCommand(TarmacTestCase):
    '''Test for tarmac.bin2.commands.Command.'''

    def test__init__(self):
        command_name = u'test'
        command = commands.CommandBase()
        command.NAME = command_name
        self.assertEqual(command.NAME, command_name)
        self.assertTrue(isinstance(command.config, TarmacConfig2))

    def test_invoke(self):
        command = commands.CommandBase()
        self.assertRaises(NotImplementedError, command.invoke)


class TestAuthCommand(TarmacTestCase):
    '''Test for tarmac.bin2.command.AuthCommand.'''

    NEEDS_SAMPLE_DATA = True

    # XXX: rockstar - 10 Jan 2010 - How do I test this with the OAuth request,
    # etc?
    #def test_invoke(self):
    #    '''Test that calling the auth command gets a Lanuchpad token.'''

    #    tmp_stdout = StringIO()
    #    old_stdout = sys.stdout
    #    sys.stdout = tmp_stdout

    #    command = AuthCommand()
    #    self.assertFalse(os.path.exists(command.config.CREDENTIALS))
    #    command.invoke()
    #    self.assertEqual(tmp_stdout.getvalue(), '')

    #    sys.stdout = old_stdout

    def test_invoke_already_authenticated(self):
        '''If the user has already been authenticated, don't try again.'''
        tmp_stdout = StringIO()
        old_stdout = sys.stdout
        sys.stdout = tmp_stdout

        command = commands.AuthCommand()
        command.invoke()
        self.assertEqual(
            tmp_stdout.getvalue(),
            'You have already been authenticated.\n')

        sys.stdout = old_stdout


class TestHelpCommand(TarmacTestCase):

    def test_invoke(self):
        tmp_stdout = StringIO()
        old_stdout = sys.stdout
        sys.stdout = tmp_stdout

        command = commands.HelpCommand()
        command.invoke()
        self.assertEqual(
            tmp_stdout.getvalue(),
            'You need help.\n')

        sys.stdout = old_stdout

class TestMergeCommand(TarmacTestCase):

    NEEDS_SAMPLE_DATA = True

    def test_invoke(self):
        tmp_stdout = StringIO()
        old_stdout = sys.stdout
        sys.stdout = tmp_stdout

        command = commands.MergeCommand()
        command.invoke()
        self.assertEqual(
            tmp_stdout.getvalue(),
            'Merging lp:~tarmac/tarmac/tarmac\n'
            'Merging lp:~tarmac/tarmac/tarmac3\n'
            'Merging lp:~tarmac/tarmac/tarmac2\n'
            'Merging lp:~tarmac/tarmac/tarmac4\n')

        sys.stdout = old_stdout
