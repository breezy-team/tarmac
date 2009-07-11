# Copyright 2009 Canonical Ltd.
#
# This file is part of Tarmac.
#
# Authors: Rodney Dawes
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

'''XDG BaseDirectory abstraction for non-Linux platforms.'''
import os
import sys

class NotSupportedError(Exception):
    '''Unsupported platform version.'''

try:
    from xdg.BaseDirectory import xdg_config_home, xdg_cache_home
except ImportError:
    if sys.platform == 'win32' or sys.platform == 'cygwin':
        xdg_config_home = os.environ.get('XDG_CONFIG_HOME', None)
        xdg_cache_home = os.environ.get('XDG_CACHE_HOME', None)
        if not xdg_config_home:
            xdg_config_home = os.environ.get('APPDATA', None)
        if not xdg_cache_home:
            xdg_cache_home = os.environ.get('TEMP', None)

        if not xdg_config_home or not xdg_cache_home:
            major, minor, build, plat, text = sys.getwindowsversion()
            if plat != 2 or major < 5:
                raise NotSupportedError('Windows %d.%d is not supported' % (
                        major, minor))
