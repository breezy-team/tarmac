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
import importlib
import logging
import os
import types

from tarmac import plugins as _mod_plugins

logger = logging.getLogger('tarmac')


def find_plugins(load_only=None):
    """Find the plugins for Tarmac.

    %load_only is a string containing the name of a single plug-in to find.
    """

    TARMAC_PLUGIN_PATHS = []
    try:
        TARMAC_PLUGIN_PATHS.extend(
            os.environ['TARMAC_PLUGIN_PATH'].split(':'))
    except KeyError:
        pass
    TARMAC_PLUGIN_PATHS.append(os.path.expanduser('~/.config/tarmac/plugins'))

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

                if load_only and _file != load_only:
                    continue

                if _file == '__init__' or (_file, full_path) in plugin_names:
                    continue
                else:
                    plugin_names.add((_file, full_path))
        except OSError:  # Usually the dir does not exist
            continue

    return plugin_names


def find_bundled_plugins():
    from importlib.resources import contents
    valid_suffixes = [suffix for suffix, mod_type, flags in imp.get_suffixes()
                      if flags == imp.PY_SOURCE]

    for name in contents("tarmac.plugins"):
        if name in ('__pycache__', 'tests'):
            continue
        if '.' in name:
            if name == '__init__.py':
                continue
            if name.startswith('.'):
                continue  # Hidden file, should be ignored.
            for suffix in valid_suffixes:
                if name.endswith(suffix):
                    name = name[:-len(suffix)]
                    break
            else:
                continue
        yield name


def load_plugins(load_only=None):
    """Find the plugins for Tarmac.

    %load_only is a string containing the name of a single plug-in to find.
    """
    plugin_names = []

    for plugin_name in find_bundled_plugins():
        try:
            if getattr(_mod_plugins, plugin_name, None) is not None:
                continue

            logger.debug('Loading plug-in: %s', plugin_name)
            importlib.import_module("tarmac.plugins.%s" % plugin_name)
        except KeyboardInterrupt:
            raise
        else:
            plugin_names.append(plugin_name)

    for plugin_name, plugin_path in find_plugins(load_only=load_only):
        try:
            if getattr(_mod_plugins, plugin_name, None) is not None:
                continue

            logger.debug('Loading plug-in: %s from %s', plugin_name,
                         plugin_path)
            _module = types.ModuleType(plugin_name)
            with open(plugin_path, "rb") as f:
                exec(compile(f.read(), plugin_path, 'exec'),
                     _module.__dict__)
            setattr(_mod_plugins, plugin_name, _module)
        except KeyboardInterrupt:
            raise
        else:
            plugin_names.append(plugin_name)
    return plugin_names
