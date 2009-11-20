'''Tests for tarmac.bin2.commands.py.'''
import unittest

from tarmac.bin2.commands import CommandRegistry


class TestCommandRegistry(unittest.TestCase):
    '''Test for tarmac.bin2.commands.CommandRegistry.'''

    def test__init__(self):
        registry = CommandRegistry()
        self.assertEqual(registry._registry, {})
