# Copyright 2013 Canonical Ltd.
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
'''Plugin utilities for Tarmac.'''

import imp
import logging
import os
import types

from tarmac import plugins as _mod_plugins

logger = logging.getLogger('tarmac')


def load_plugins(load_only=None):
    '''Load the plugins for Tarmac.'''

    TARMAC_PLUGIN_PATHS = [
        os.path.expanduser('~/.config/tarmac/plugins'),
        os.path.join(os.path.dirname(__file__), 'plugins'),
    ]
    try:
        TARMAC_PLUGIN_PATHS.extend(
            os.environ['TARMAC_PLUGIN_PATH'].split(':'))
    except KeyError:
        pass

    logger.debug('Using plug-in paths: %s' % TARMAC_PLUGIN_PATHS)
    valid_suffixes = [suffix for suffix, mod_type, flags in imp.get_suffixes()
                      if flags == imp.PY_SOURCE]
    package_entries = ['__init__' + suffix for suffix in valid_suffixes]

    plugin_names = set()
    for path in TARMAC_PLUGIN_PATHS:
        try:
            for _file in os.listdir(path):
                full_path = os.path.join(path, _file)
                if os.path.isdir(full_path):
                    _file = os.path.basename(full_path)
                    for entry in package_entries:
                        if os.path.isfile(os.path.join(full_path, entry)):
                            # This directory is definitely a package
                            full_path = os.path.join(full_path, entry)
                            break
                        else:
                            continue

                else:
                    if _file.startswith('.'):
                        continue  # Hidden file, should be ignored.
                    for suffix in valid_suffixes:
                        if _file.endswith(suffix):
                            _file = _file[:-len(suffix)]
                            break
                        else:
                            continue
                    if '.' in _file:
                        logger.debug('Skipping file `%s` for plug-in.' % _file)
                        continue

                if _file != load_only:
                    continue

                if _file == '__init__':
                    continue
                elif getattr(_mod_plugins, _file, None):
                    continue  # Plugin is already loaded.
                else:
                    plugin_names.add((_file, full_path))
        except OSError:  # Usually the dir does not exist
            continue

    for plugin_info in plugin_names:
        try:
            logger.debug('Loading plug-in: %s' % plugin_info[1])
            _module = types.ModuleType(plugin_info[0])
            execfile(plugin_info[1], _module.__dict__)
            print(_module)
            setattr(_mod_plugins, plugin_info[0], _module)
        except KeyboardInterrupt:
            raise
