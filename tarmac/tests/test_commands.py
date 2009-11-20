'''Tests for tarmac.bin2.commands.py.'''
import unittest

from tarmac.bin2.commands import Command, CommandRegistry


class TestCommandRegistry(unittest.TestCase):
    '''Test for tarmac.bin2.commands.CommandRegistry.'''

    def test__init__(self):
        registry = CommandRegistry()
        self.assertEqual(registry._registry, {})

    def test_run(self):
        registry = CommandRegistry()
        registry.run()


class TestCommand(unittest.TestCase):
    '''Test for tarmac.bin2.commands.Command.'''

    def test__init__(self):
        command_name = u'test'
        command = Command(command_name)
        self.assertEqual(command.name, command_name)

    def test_invoke(self):
        command = Command('test')
        self.assertRaises(NotImplementedError, command.invoke)
