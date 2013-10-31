'''Tests for tarmac.bin.registry.'''
from bzrlib.errors import BzrCommandError

from tarmac.bin.commands import cmd_authenticate, TarmacCommand
from tarmac.bin.registry import CommandRegistry
from tarmac.exceptions import CommandNotFound
from tarmac.tests import TarmacTestCase
from tarmac.tests import cmd_mock, MockModule


class TestCommandRegistry(TarmacTestCase):
    '''Test for tarmac.bin.commands.CommandRegistry.'''

    def test__init__(self):
        registry = CommandRegistry(config=self.config)
        self.assertEqual(registry._registry, {})

    def test__run(self):
        registry = CommandRegistry(config=self.config)
        self.assertRaises(BzrCommandError, registry._run, ['nothing'])

    def test_register_command(self):
        registry = CommandRegistry(config=self.config)
        command = TarmacCommand(registry)
        registry.register_command(u'test', command)
        self.assertEqual(registry._registry,
            {'test': command})

    def test__get_command(self):
        registry = CommandRegistry(config=self.config)
        registry.register_command('authenticate', cmd_authenticate)
        looked_up_command = registry._get_command(cmd_authenticate,
                                                  'authenticate')
        self.assertTrue(
            isinstance(looked_up_command, cmd_authenticate))

    def test__get_command_notfound(self):
        registry = CommandRegistry(config=self.config)
        self.assertRaises(
            CommandNotFound,
            registry._get_command, TarmacCommand(registry), u'test2')

    def test_register_from_module(self):
        registry = CommandRegistry(config=self.config)
        registry.register_from_module(MockModule())
        mock_command = registry._get_command(TarmacCommand, 'mock')
        self.assertTrue(isinstance(mock_command, cmd_mock))

    def DISABLEDtest__list_commands(self):
        registry = CommandRegistry(config=self.config)
        registry.register_command('authenticate', cmd_authenticate)
        names = {}
        names = registry._list_commands(names)
        self.assertEqual(names.iterkeys(), registry._commands.iterkeys())
