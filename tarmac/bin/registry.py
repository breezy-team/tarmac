'''A command registry for Tarmac commands.'''
import sys

from bzrlib.commands import Command, run_bzr
from bzrlib.errors import BzrCommandError

from tarmac.config import TarmacConfig
from tarmac.exceptions import CommandNotFound


class CommandRegistry(object):
    '''Class for handling command dispatch.'''

    def __init__(self, config=None):
        self._registry = {}
        self.config = config
        if self.config is None:
            self.config = TarmacConfig()

    def _get_command(self, command, name):
        '''Return the command.'''
        _command = None
        try:
            _command = self._registry[name]
        except KeyError:
            for cmd in self._registry.itervalues():
                if name in cmd.aliases:
                    _command = cmd
                    break

        if not _command:
            raise CommandNotFound
        return _command(self)

    # XXX: rockstar - This is entirely untested right now, since I don't know
    # how it works.
    def _list_commands(self, names):
        names.update(self._registry.iterkeys())
        return names

    def _run(self, args):
        '''Execute the command.'''
        run_bzr(args)

    def install_hooks(self):
        '''Use the bzrlib Command support for running commands.'''
        Command.hooks.install_named_hook(
            'get_command', self._get_command, 'Tarmac commands')
        Command.hooks.install_named_hook(
            'list_commands', self._list_commands, 'Tarmac commands')

    def run(self, args):
        '''Execute the command.'''
        try:
            self._run(args)
        except BzrCommandError, e:
            sys.exit('tarmac: ERROR: ' + str(e))

    def register_command(self, name, command_class):
        '''Register a command in the registry.'''
        try:
            self._registry[name] = command_class
        except AttributeError:
            # The NAME attribute isn't set, so is invalid
            return

    def register_from_module(self, module):

        for name in module.__dict__:
            if name.startswith("cmd_"):
                sanitized_name = name[4:].replace("_", "-")
                self.register_command(sanitized_name, module.__dict__[name])
