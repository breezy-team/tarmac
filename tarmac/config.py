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

import logging
import os
from configparser import ConfigParser, NoSectionError

from breezy.tree import Tree
from breezy.transport import NoSuchFile

from tarmac.xdgdirs import xdg_config_home, xdg_cache_home


class TarmacConfig(ConfigParser):
    '''A class for handling configuration.'''

    def __init__(self):
        self.logger = logging.getLogger('tarmac')
        DEFAULTS = {
            'log_file': os.path.join(self.CONFIG_HOME, 'tarmac.log'),
            }

        ConfigParser.__init__(self)

        self._check_config_dirs()
        self.logger.info('Reading configuration from %s', self.CONFIG_FILE)
        self.read(self.CONFIG_FILE)

        if not self.has_section('Tarmac'):
            self.add_section('Tarmac')

        if not self.has_option('Tarmac', 'log_file'):
            self.set('Tarmac', 'log_file', DEFAULTS['log_file'])

        for key, val in self.items('Tarmac'):
            setattr(self, key, val)

    def set(self, section, option, value):
        """Wrap the set method, so we can tweak our attrs."""
        ConfigParser.set(self, section, option, str(value))
        if section == 'Tarmac':
            setattr(self, option, value)

    def remove_option(self, section, option):
        """Wrap the remove_option method so we can tweak our attrs."""
        ConfigParser.remove_option(self, section, option)
        if section == 'Tarmac':
            delattr(self, option)

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
        return [section for section in self.sections() if
                section.startswith('lp:')]

    def _check_config_dirs(self):
        '''Create the configuration directory if it does not exist.'''
        if not os.path.exists(self.CONFIG_HOME):
            os.makedirs(self.CONFIG_HOME)
        if not os.path.exists(self.CACHE_HOME):
            os.makedirs(self.CACHE_HOME)
        pid_dir = os.path.dirname(self.PID_FILE)
        if not os.path.exists(pid_dir):
            os.makedirs(pid_dir)

    @property
    def rejected_branch_status(self):
        return self['Tarmac'].get('rejected_branch_status')


class TreeConfig:
    """A Tarmac config that lives in a tree."""

    def __init__(self, text):
        self._config = ConfigParser()
        self._config.read_string(text)

    def __getitem__(self, attr):
        return self._config['Tarmac'][attr]

    def get(self, attr, default=None):
        '''A convenient method for getting a config key that may be missing.

        Defaults to None if the key is not set.
        '''
        try:
            return self[attr]
        except KeyError:
            return default

    @classmethod
    def from_tree(cls, tree: Tree):
        try:
            text = tree.get_file_text('tarmac.conf')
            return cls(text.decode('utf-8'))
        except NoSuchFile:
            return None


class BranchConfig:
    """A Branch specific config.

    Instead of providing the whole config for branches, it is better to provide
    it with only its specific config vars.
    """

    def __init__(self, branch_name, config):
        self._branch_name = branch_name
        self._config = config

    def __getitem__(self, attr):
        try:
            return self._config[self._branch_name][attr]
        except NoSectionError as e:
            raise KeyError(attr) from e

    def get(self, attr, default=None):
        '''A convenient method for getting a config key that may be missing.

        Defaults to None if the key is not set.
        '''
        try:
            section = self._config[self._branch_name]
        except (NoSectionError, KeyError):
            return default
        return section.get(attr, default)


class StackedConfig:
    """A Config that queries other configs.
    """

    def __init__(self, others):
        self._others = others

    def __getitem__(self, attr):
        for other in self._others:
            try:
                return other[attr]
            except KeyError:
                pass
        else:
            raise KeyError(attr)

    def get(self, attr, default=None):
        try:
            return self[attr]
        except KeyError:
            return default
