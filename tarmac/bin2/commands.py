'''Command handling for Tarmac.'''

class Command(object):
    '''A command class.'''

    def __init__(self, name):
        self.name = name

class CommandRegistry():
    '''Class for handling command dispatch.'''

    def __init__(self):
        self._registry = {}

    def run(self):
        '''Execute the command.'''


def main():
    '''Main script handler.'''
    dispatch = CommandDispatch()
    dispatch.run()
