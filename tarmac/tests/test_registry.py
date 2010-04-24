'''Tests for tarmac.bin.registry.'''
import unittest

from bzrlib.errors import BzrCommandError

from tarmac.bin.commands import cmd_auth, TarmacCommand
from tarmac.bin.registry import CommandRegistry
from tarmac.exceptions import CommandNotFound
from tarmac.tests.mock import cmd_mock, MockModule

class TestCommandRegistry(unittest.TestCase):
    '''Test for tarmac.bin.commands.CommandRegistry.'''

    def test__init__(self):
        registry = CommandRegistry()
        self.assertEqual(registry._registry, {})

    def test__run(self):
        registry = CommandRegistry()
        self.assertRaises(BzrCommandError, registry._run, ['nothing'])

    def test_register_command(self):
        command = TarmacCommand()
        registry = CommandRegistry()
        registry.register_command(u'test', command)
        self.assertEqual(registry._registry,
            {'test': command})

    def test__get_command(self):
        registry = CommandRegistry()
        registry.register_command('auth', cmd_auth)
        looked_up_command = registry._get_command(cmd_auth, 'auth')
        self.assertTrue(
            isinstance(looked_up_command, cmd_auth))

    def test__get_command_notfound(self):
        registry = CommandRegistry()
        self.assertRaises(
            CommandNotFound,
            registry._get_command, TarmacCommand(), u'test2')

    def test_register_from_module(self):
        registry = CommandRegistry()
        registry.register_from_module(MockModule())
        mock_command = registry._get_command(TarmacCommand, 'mock')
        self.assertTrue(isinstance(mock_command, cmd_mock))

    def DISABLEDtest__list_commands(self):
        registry = CommandRegistry()
        registry.register_command(AuthCommand)
        names = {}
        names = registry._list_commands(names)
        self.assertEqual(names.iterkeys(), registry._commands.iterkeys())
