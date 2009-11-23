'''Tests for tarmac.bin2.commands.py.'''
from cStringIO import StringIO
import sys
import unittest

from tarmac.bin2.commands import AuthCommand, Command, CommandRegistry
from tarmac.exceptions import CommandNotFound


class TestCommandRegistry(unittest.TestCase):
    '''Test for tarmac.bin2.commands.CommandRegistry.'''

    def test__init__(self):
        registry = CommandRegistry()
        self.assertEqual(registry._registry, {})

    def test_run(self):
        registry = CommandRegistry()
        self.assertRaises(CommandNotFound, registry.run)

    def test_register_command(self):
        command = Command()
        command.NAME = u'test'
        registry = CommandRegistry()
        registry.register_command(command)
        self.assertEqual(registry._registry,
            {'test': command})

    def test__lookup_command(self):
        command = Command()
        command.NAME = u'test'
        registry = CommandRegistry()
        registry.register_command(command)
        self.assertEqual(
            registry._lookup_command(u'test'),
            command)

    def test__lookup_command_notfound(self):
        command = Command()
        command.NAME = u'test'
        registry = CommandRegistry()
        registry.register_command(command)
        self.assertRaises(
            CommandNotFound,
            registry._lookup_command, u'test2')


class TestCommand(unittest.TestCase):
    '''Test for tarmac.bin2.commands.Command.'''

    def test__init__(self):
        command_name = u'test'
        command = Command()
        command.NAME = command_name
        self.assertEqual(command.NAME, command_name)

    def test_invoke(self):
        command = Command()
        command.NAME = u'test'
        self.assertRaises(NotImplementedError, command.invoke)


class TestAuthCommand(unittest.TestCase):
    '''Test for tarmac.bin2.command.AuthCommand.'''

    def test_invoke(self):
        tmp_stdout = StringIO()
        old_stdout = sys.stdout
        sys.stdout = tmp_stdout

        command = AuthCommand()
        command.invoke()
        self.assertEqual(tmp_stdout.getvalue(), 'authenticated\n')

        sys.stdout = old_stdout
