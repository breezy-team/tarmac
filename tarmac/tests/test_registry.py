'''Tests for tarmac.bin2.registry.'''
import unittest

from tarmac.bin2.commands import AuthCommand, Command
from tarmac.bin2.registry import CommandRegistry
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
        registry = CommandRegistry()
        registry.register_command(AuthCommand)
        looked_up_command = registry._lookup_command(object(), u'auth')
        self.assertTrue(
            isinstance(looked_up_command, AuthCommand))

    def test__lookup_command_notfound(self):
        registry = CommandRegistry()
        self.assertRaises(
            CommandNotFound,
            registry._lookup_command, object(), u'test2')



