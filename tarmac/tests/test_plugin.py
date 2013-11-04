# Copyright 2013 Canonical, Ltd.
#
# Tarmac is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# Tarmac is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tarmac.  If not, see <http://www.gnu.org/licenses/>.
"""Tests for the plug-in loader code."""

import os

from mock import ANY, patch
from tarmac import plugin
from tarmac import plugins as _mod_plugins
from tarmac.tests import TarmacTestCase


class PluginTestCase(TarmacTestCase):
    """Test the plug-in loader."""

    def _patch_env(self, envvar, value):
        """Patch %envvar with %value, and revert when done."""
        old_val = os.environ.get(envvar, None)
        if old_val is None:
            self.addCleanup(os.environ.pop, envvar, None)
        else:
            self.addCleanup(setitem, os.environ, envvar, old_val)

        if value is None:
            os.environ.pop(envvar, None)
        else:
            os.environ[envvar] = value

    @patch('tarmac.plugin.execfile', create=True)
    def test_load_plugins_external(self, mocked):
        """Test that external plug-ins load."""
        plugin_path = os.path.join(os.path.dirname(__file__), 'plugins')
        self._patch_env('TARMAC_PLUGIN_PATH', plugin_path)
        plugin_name = 'testplugin'
        plugin_file = os.path.join(plugin_path, plugin_name + '.py')
        self.addCleanup(delattr, _mod_plugins, plugin_name)
        plugin.load_plugins(load_only=plugin_name)
        mocked.assert_called_once_with(plugin_file, ANY)

    @patch('tarmac.plugin.execfile', create=True)
    def test_load_plugins_once_only(self, mocked):
        """Test that external plug-ins load."""
        plugin_path = os.path.join(os.path.dirname(__file__), 'plugins')
        self._patch_env('TARMAC_PLUGIN_PATH',
                        '%s:%s' % (plugin_path, plugin_path))
        plugin_name = 'testplugin'
        plugin_file = os.path.join(plugin_path, plugin_name + '.py')
        self.addCleanup(delattr, _mod_plugins, plugin_name)
        plugin.load_plugins(load_only=plugin_name)
        mocked.assert_called_once_with(plugin_file, ANY)

    @patch('tarmac.plugin.execfile', create=True)
    def test_load_plugins_package(self, mocked):
        """Test that package plug-ins load."""
        plugin_path = os.path.join(os.path.dirname(__file__), 'plugins')
        self._patch_env('TARMAC_PLUGIN_PATH', plugin_path)
        plugin_name = 'pkgplugin'
        plugin_file = os.path.join(plugin_path, os.path.join(
            plugin_name, '__init__.py'))
        self.addCleanup(delattr, _mod_plugins, plugin_name)
        plugin.load_plugins(load_only=plugin_name)
        mocked.assert_called_once_with(plugin_file, ANY)
