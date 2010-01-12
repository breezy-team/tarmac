'''A command registry for Tarmac commands.'''
import sys

from bzrlib.commands import Command

from tarmac.exceptions import CommandNotFound


class CommandRegistry():
    '''Class for handling command dispatch.'''

    def __init__(self):
        self._registry = {}

    def install_hooks(self):
        '''Use the bzrlib Command support for running commands.'''
        Command.hooks.install_named_hook(
            'get_command', self._get_command, 'Tarmac commands')

    def run(self):
        '''Execute the command.'''
        try:
            command_name = sys.argv[1]
        except IndexError:
            command_name = 'help'

    def register_command(self, command):
        '''Register a command in the registry.'''
        try:
            self._registry[command.NAME] = command
        except AttributeError:
            # The NAME attribute isn't set, so is invalid
            return

    def _get_command(self, command, name):
        '''Return the command.'''
        try:
            _command = self._registry[name]()
        except KeyError:
            raise CommandNotFound

        return _command

    def register_from_module(self, module):
        for item in module.__dict__:
            if item.endswith("Command"):
                self.register_command(module.__dict__[item])
