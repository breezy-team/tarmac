'''Command handling for Tarmac.'''
import os
import sys

from tarmac.config import TarmacConfig2
from tarmac.exceptions import CommandNotFound
from tarmac.launchpad import get_launchpad_object


class CommandBase(object):
    '''A command class.'''

    NAME = None

    def __init__(self):
        self.config = TarmacConfig2()

    def invoke(self):
        '''Actually run the command.'''
        raise NotImplementedError

    def get_launchpad_object(self):
        '''Return a Launchpad object for making API requests.'''
        # XXX: rockstar - I assume that the code from
        # tarmac.launchpad.get_launchpad_object can go away because of this.
        return get_launchpad_object(self.config)


class AuthCommand(CommandBase):

    NAME = 'auth'

    def invoke(self):
        if os.path.exists(self.config.CREDENTIALS):
            print 'You have already been authenticated.'
        else:
            launchpad = self.get_launchpad_object()
