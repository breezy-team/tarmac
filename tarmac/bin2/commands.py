'''Command handling for Tarmac.'''
import os
import sys

from launchpadlib.launchpad import (Credentials, Launchpad, EDGE_SERVICE_ROOT,
    STAGING_SERVICE_ROOT)

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

    def get_launchpad_object(self, filename=None, staging=True):
        '''Return a Launchpad object for making API requests.'''
        # XXX: rockstar - 2009 Dec 13 - Ideally, we should be using
        # Launchpad.login_with, but currently, it doesn't support the option of
        # putting the credentials file somewhere other than where the cache
        # goes, and that's kinda nasty (and a security issue according to
        # Kees).
        if not filename:
            filename = self.config.CREDENTIALS

        if staging:
            SERVICE_ROOT = STAGING_SERVICE_ROOT
        else:
            SERVICE_ROOT = EDGE_SERVICE_ROOT

        if not os.path.exists(filename):
            launchpad = Launchpad.get_token_and_login(
                'Tarmac', SERVICE_ROOT, self.config.CACHE_HOME)
            launchpad.credentials.save(file(filename, 'w'))
        else:
            credentials = Credentials()
            credentials.load(open(filename))
            launchpad = Launchpad(
                credentials, SERVICE_ROOT, self.config.CACHE_HOME)
        return launchpad


class AuthCommand(CommandBase):

    NAME = 'auth'

    def invoke(self):
        if os.path.exists(self.config.CREDENTIALS):
            print 'You have already been authenticated.'
        else:
            launchpad = self.get_launchpad_object()

class HelpCommand(CommandBase):

    NAME = 'help'

    def invoke(self):
        print 'You need help.'


class MergeCommand(CommandBase):

    NAME = 'merge'

    def invoke(self):
        print 'Merging.'
