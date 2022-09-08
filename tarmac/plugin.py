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


def find_plugins(load_only=None):
    """Find the plugins for Tarmac.

    %load_only is a string containing the name of a single plug-in to find.
    """

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
                if _file == '__pycache__':
                    continue
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

                if  load_only and _file != load_only:
                    continue

                if _file == '__init__' or (_file, full_path) in plugin_names:
                    continue
                else:
                    plugin_names.add((_file, full_path))
        except OSError:  # Usually the dir does not exist
            continue

    return plugin_names


def load_plugins(load_only=None):
    """Find the plugins for Tarmac.

    %load_only is a string containing the name of a single plug-in to find.
    """
    for plugin_info in find_plugins(load_only=load_only):
        try:
            if getattr(_mod_plugins, plugin_info[0], None) is not None:
                continue

            logger.debug('Loading plug-in: %s' % plugin_info[1])
            _module = types.ModuleType(plugin_info[0])
            with open(plugin_info[1], "rb") as f:
                exec(compile(f.read(), plugin_info[1], 'exec'), _module.__dict__)
            setattr(_mod_plugins, plugin_info[0], _module)
        except KeyboardInterrupt:
            raise
