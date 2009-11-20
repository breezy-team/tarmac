'''Command handling for Tarmac.'''
from tarmac.exceptions import CommandNotFound

class Command(object):
    '''A command class.'''

    NAME = None

    def invoke(self):
        '''Actually run the command.'''
        raise NotImplementedError


class AuthCommand(object):

    NAME = 'auth'

    def __init__(self):
        Command.__init__(self)

    def invoke(self):
        print 'authenticated'


class CommandRegistry():
    '''Class for handling command dispatch.'''

    def __init__(self):
        self._registry = {}

    def run(self):
        '''Execute the command.'''

    def register_command(self, command):
        '''Register a command in the registry.'''
        self._registry[command.NAME] = command

    def _lookup_command(self, name):
        '''Look up the command by its name.'''
        try:
            return self._registry[name]
        except KeyError:
            raise CommandNotFound


def main():
    '''Main script handler.'''
    registry = CommandRegistry()
    registry.register_command(AuthCommand())
    registry.run()
