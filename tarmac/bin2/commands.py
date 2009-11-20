'''Command handling for Tarmac.'''

class Command(object):
    '''A command class.'''

    def __init__(self, name):
        self.name = name

    def invoke(self):
        '''Actually run the command.'''
        raise NotImplementedError

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
