# Copyright 2014 Canonical, Ltd.
#
# This file is part of Tarmac.
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
"""Tests for base/abstract TarmacPlugin class."""

from tarmac.plugins import TarmacPlugin
from tarmac.tests import Thing, TarmacTestCase


class TestTarmacPlugin(TarmacTestCase):
    """Test the tarmacplugin abstract class."""

    def test_get_config_missing(self):
        """get_config returns default values."""
        value = TarmacPlugin.get_config("foo", "default", Thing())
        self.assertEqual(value, "default")
        value = TarmacPlugin.get_config("foo", None, Thing(config=None))
        self.assertEqual(value, None)

    def test_get_config_basic(self):
        """get_config returns values."""
        value = TarmacPlugin.get_config(
            "foo", "default", Thing(config=Thing(foo="bar")))
        self.assertEqual(value, "bar")

    def test_get_config_multiple(self):
        """get_config returns values from multiple objects."""
        value = TarmacPlugin.get_config(
            "foo", "default",
            Thing(config=Thing(bar="bar")),
            Thing(config=Thing(foo="first")),
            Thing(config=Thing(foo="second")))
        self.assertEqual(value, "first")
