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
"""Tarmac plug-in for testing the plug-in loader."""

from tarmac.plugins import TarmacPlugin


class TestPlugin(TarmacPlugin):
    """Tarmac plug-in for testing the loader."""

    def run(self, *args, **kwargs):
        """Do nothing."""
