'''Tests for tarmac.bin2.commands.py.'''
from cStringIO import StringIO
import os
import sys
import unittest

from tarmac.bin2.commands import AuthCommand, CommandBase
from tarmac.config import TarmacConfig2
from tarmac.exceptions import CommandNotFound


class TestCommand(unittest.TestCase):
    '''Test for tarmac.bin2.commands.Command.'''

    def test__init__(self):
        command_name = u'test'
        command = CommandBase()
        command.NAME = command_name
        self.assertEqual(command.NAME, command_name)
        self.assertTrue(isinstance(command.config, TarmacConfig2))

    def test_invoke(self):
        command = CommandBase()
        self.assertRaises(NotImplementedError, command.invoke)


class TestAuthCommand(unittest.TestCase):
    '''Test for tarmac.bin2.command.AuthCommand.'''

    def test_invoke(self):
        '''Test that calling the auth command gets a Lanuchpad token.'''

        tmp_stdout = StringIO()
        old_stdout = sys.stdout
        sys.stdout = tmp_stdout

        command = AuthCommand()
        self.assertFalse(os.path.exists(command.config.CREDENTIALS))
        command.invoke()
        self.assertEqual(tmp_stdout.getvalue(), 'authenticated\n')

        sys.stdout = old_stdout
