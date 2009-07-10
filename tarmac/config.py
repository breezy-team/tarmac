# Copyright 2009 Paul Hummer
# Copyright 2009 Canonical Ltd.
#
# This file is part of Tarmac.
#
# Authors: Paul Hummer
#          Rodney Dawes
#
# Tarmac is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by
# the Free Software Foundation.
#
# Tarmac is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tarmac.  If not, see <http://www.gnu.org/licenses/>.

'''Configuration handler.'''
# pylint: disable-msg=C0103
import os
from ConfigParser import NoSectionError, NoOptionError
from ConfigParser import SafeConfigParser as ConfigParser
from xdg.BaseDirectory import xdg_config_home, xdg_cache_home

class TarmacConfig:
    '''A configuration class.'''

    def __init__(self, project=None):
        '''The config options are based on ~/.config/tarmac.

        If the configuration directories don't exist, they will be created.
        The section parameter is for coping with multiple projects in a single
        config.
        '''
        self.CONFIG_HOME = os.path.join(xdg_config_home, 'tarmac')
        self.CACHE_HOME = os.path.join(xdg_cache_home, 'tarmac')
        self.PID_FILE = '/var/tmp/tarmac-%(project)s' % {'project': project }
        self.CREDENTIALS = os.path.join(self.CACHE_HOME, 'credentials')

        self._check_config_dirs()
        self._CONFIG_FILE = os.path.join(self.CONFIG_HOME, 'tarmac.conf')
        self._CONFIG = ConfigParser()
        self._CONFIG.read(self._CONFIG_FILE)
        self._PROJECT = project

    def _check_config_dirs(self):
        '''Create the configuration directory if it doesn't exist.'''
        if not os.path.exists(config.CONFIG_HOME):
            os.makedirs(config.CONFIG_HOME)
        if not os.path.exists(config.CACHE_HOME):
            os.makedirs(config.CACHE_HOME)

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

