'''A command registry for Tarmac commands.'''
import sys

from bzrlib.commands import Command, run_bzr

from tarmac.exceptions import CommandNotFound


class CommandRegistry():
    '''Class for handling command dispatch.'''

    def __init__(self):
        self._registry = {}

    def install_hooks(self):
        '''Use the bzrlib Command support for running commands.'''
        Command.hooks.install_named_hook(
            'get_command', self._get_command, 'Tarmac commands')
        Command.hooks.install_name_hook(
            'list_commands', self._list_commands, 'Tarmac commands')

    def run(self):
        '''Execute the command.'''
        try:
            command_name = sys.argv[1]
        except IndexError:
            command_name = 'help'
        run_bzr(sys.argv[1:])

    def register_command(self, name, command_class):
        '''Register a command in the registry.'''
        try:
            self._registry[name] = command_class
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

    # TODO: rockstar - This is entirely untested right now, since I don't know
    # how it works.
    def _list_commands(self, names):
        names.update(self._registry.iterkeys())
        return names

    def register_from_module(self, module):

        for name in module.__dict__:
            if name.startswith("cmd_"):
                sanitized_name = name[4:].replace("_", "-")
                self.register_command(sanitized_name, module.__dict__[name])
            elif name.startswith("topic_"):
                sanitized_name = name[6:].replace("_", "-")
                self.register_help_topic(sanitized_name, module.__dict__[name])

        for item in module.__dict__:
            if item.startswith("cmd"):
                self.register_command(module.__dict__[item])
