# Copyright 2009 Paul Hummer
# Copyright 2009 Canonical Ltd.
#
# This file is part of Tarmac.
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
__metaclass__ = type

import os
import sys
from ConfigParser import NoSectionError, NoOptionError
from ConfigParser import SafeConfigParser as ConfigParser
from tarmac.xdgdirs import xdg_config_home, xdg_cache_home


class TarmacConfig2(ConfigParser):
    '''A class for handling configuration.'''

    def __init__(self):
        DEFAULTS = {
            'log_file': os.path.abspath('.'),
            'tree_dir': None}

        ConfigParser.__init__(self, DEFAULTS)
        self._check_config_dirs()
        self.read(self.CONFIG_FILE)

    @property
    def CONFIG_HOME(self):
        '''Return the base dir for the config.'''
        try:
            return os.environ['TARMAC_CONFIG_HOME']
        except KeyError:
            return os.path.join(xdg_config_home, 'tarmac')

    @property
    def CACHE_HOME(self):
        '''Return the base dir for cache.'''
        try:
            return os.environ['TARMAC_CACHE_HOME']
        except KeyError:
            return os.path.join(xdg_cache_home, 'tarmac')

    @property
    def PID_FILE(self):
        '''Return the path to the pid file.'''
        try:
            return os.environ['TARMAC_PID_FILE']
        except KeyError:
            return os.path.join(self.CACHE_HOME, 'tarmac.pid')

    @property
    def CREDENTIALS(self):
        '''Return the path to the credentials.'''
        try:
            return os.environ['TARMAC_CREDENTIALS']
        except KeyError:
            return os.path.join(self.CONFIG_HOME, 'credentials')

    @property
    def CONFIG_FILE(self):
        '''Return the path to the config file itself.'''
        return os.path.join(self.CONFIG_HOME, 'tarmac.conf')

    @property
    def branches(self):
        '''Return all the branches in the config.'''
        return self.sections()

    def _check_config_dirs(self):
        '''Create the configuration directory if it doesn't exist.'''
        if not os.path.exists(self.CONFIG_HOME):
            os.makedirs(self.CONFIG_HOME)
        if not os.path.exists(self.CACHE_HOME):
            os.makedirs(self.CACHE_HOME)
        pid_dir = os.path.dirname(self.PID_FILE)
        if not os.path.exists(pid_dir):
            os.makedirs(pid_dir)


class BranchConfig:
    '''A Branch specific config.

    Instead of providing the whole config for branches, it's better to provide
    it with only its specific config vars.
    '''

    def __init__(self, branch_name, config):
        for key, val in config.items(branch_name):
            setattr(self, key, val)


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
        self.PID_FILE = os.path.join(
            self.CACHE_HOME, 'tarmac-%(project)s' % {'project': project })
        self.CREDENTIALS = os.path.join(self.CONFIG_HOME, 'credentials')

        self._check_config_dirs()
        self._CONFIG_FILE = os.path.join(self.CONFIG_HOME, 'tarmac.conf')
        self._CONFIG = ConfigParser()
        self._CONFIG.read(self._CONFIG_FILE)
        self._PROJECT = project

    def _check_config_dirs(self):
        '''Create the configuration directory if it doesn't exist.'''
        if not os.path.exists(self.CONFIG_HOME):
            os.makedirs(self.CONFIG_HOME)
        if not os.path.exists(self.CACHE_HOME):
            os.makedirs(self.CACHE_HOME)
        pid_dir = os.path.dirname(self.PID_FILE)
        if not os.path.exists(pid_dir):
            os.makedirs(pid_dir)

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

    @property
    def tree_dir(self):
        '''Get the cached tree dir so no superfluous fetching is needed.'''
        return self.get('tree_dir')

    def get(self, key):
        '''Get a config value for the given key.'''
        try:
            return self._CONFIG.get(self._PROJECT, key)
        except (NoOptionError, NoSectionError):
            return None

