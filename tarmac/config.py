# Copyright 2009 Paul Hummer - See LICENSE
'''Configuration handler.'''
# pylint: disable-msg=C0103
import os
from ConfigParser import NoSectionError, NoOptionError
from ConfigParser import SafeConfigParser as ConfigParser


class TarmacConfig:
    '''A configuration class.'''

    def __init__(self, project=None):
        '''The config options are based on ~/.config/tarmac.

        If the configuration directories don't exist, they will be created.
        The section parameter is for coping with multiple projects in a single
        config.
        '''
        self.CONFIG_HOME = os.path.expanduser('~/.config/tarmac')
        self.PID_FILE = '/var/tmp/tarmac-%(project)s' % {'project': project }
        self.CREDENTIALS = os.path.join(self.CONFIG_HOME, 'credentials')

        self.CACHEDIR = os.path.join(self.CONFIG_HOME, 'cachedir')

        self._check_config_dirs()
        self._CONFIG_FILE = os.path.join(self.CONFIG_HOME, 'tarmac.conf')
        self._CONFIG = ConfigParser()
        self._CONFIG.read(self._CONFIG_FILE)
        self._PROJECT = project

    def _check_config_dirs(self):
        '''Create the configuration directory if it doesn't exist.'''
        if not os.path.exists(os.path.expanduser('~/.config')):
            os.mkdir(os.path.expanduser('~/.config'))
        if not os.path.exists(os.path.expanduser('~/.config/tarmac')):
            os.mkdir(os.path.expanduser('~/.config/tarmac'))
        if not os.path.exists(os.path.expanduser('~/.config/tarmac/cachedir')):
            os.mkdir(os.path.expanduser('~/.config/tarmac/cachedir'))

    @property
    def commit_message_template(self):
        '''Return the commit_message_template.'''
        return self.get('commit_message_template')

    @property
    def test_command(self):
        '''Get the test_command from the stored config.'''
        return self.get('test_command')

    @property
    def cia_server(self):
        '''Server for the CIA plugin.'''
        return self.get('cia_server')

    @property
    def cia_project(self):
        '''Project for the CIA plugin.'''
        return self.get('cia_project')

    @property
    def log_file(self):
        '''Get the log_file from config or return a default.'''
        try:
            return self._CONFIG.get(self._PROJECT, 'log_file')
        except (NoOptionError, NoSectionError):
            return os.path.join(self.CONFIG_HOME, self._PROJECT)

    def get(self, key):
        '''Get a config value for the given key.'''
        try:
            return self._CONFIG.get(self._PROJECT, key)
        except (NoOptionError, NoSectionError):
            return None

