'''A command registry for Tarmac commands.'''
import sys

from tarmac.exceptions import CommandNotFound


class CommandRegistry():
    '''Class for handling command dispatch.'''

    def __init__(self):
        self._registry = {}

    def run(self):
        '''Execute the command.'''
        command = sys.argv[1]
        self._lookup_command(command).invoke()

    def register_command(self, command):
        '''Register a command in the registry.'''
        self._registry[command.NAME] = command

    def _lookup_command(self, name):
        '''Look up the command by its name.'''
        try:
            return self._registry[name]
        except KeyError:
            raise CommandNotFound
