'''Command handling for Tarmac.'''
import sys

from tarmac.config import TarmacConfig2
from tarmac.exceptions import CommandNotFound

class CommandBase(object):
    '''A command class.'''

    NAME = None

    def __init__(self):
        self.config = TarmacConfig2()

    def invoke(self):
        '''Actually run the command.'''
        raise NotImplementedError


class AuthCommand(CommandBase):

    NAME = 'auth'

    def invoke(self):
        print 'authenticated'
