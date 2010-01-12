'''Tests for tarmac.bin2.registry.'''
import unittest

from tarmac.bin2.commands import AuthCommand, TarmacCommand
from tarmac.bin2.registry import CommandRegistry
from tarmac.exceptions import CommandNotFound
from tarmac.tests.mock import MockCommand, MockModule

class TestCommandRegistry(unittest.TestCase):
    '''Test for tarmac.bin2.commands.CommandRegistry.'''

    def test__init__(self):
        registry = CommandRegistry()
        self.assertEqual(registry._registry, {})

    def test_run(self):
        registry = CommandRegistry()
        self.assertRaises(CommandNotFound, registry.run)

    def test_register_command(self):
        command = TarmacCommand()
        command.NAME = u'test'
        registry = CommandRegistry()
        registry.register_command(command)
        self.assertEqual(registry._registry,
            {'test': command})

    def test__get_command(self):
        registry = CommandRegistry()
        registry.register_command(AuthCommand)
        looked_up_command = registry._get_command(AuthCommand(), u'auth')
        self.assertTrue(
            isinstance(looked_up_command, AuthCommand))

    def test__get_command_notfound(self):
        registry = CommandRegistry()
        self.assertRaises(
            CommandNotFound,
            registry._get_command, TarmacCommand(), u'test2')

    def test_register_from_module(self):
        registry = CommandRegistry()
        registry.register_from_module(MockModule())
        mock_command = registry._get_command(TarmacCommand(), 'mock')
        self.assertTrue(isinstance(mock_command, MockCommand))
