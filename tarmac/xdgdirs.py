# Copyright 2009 Canonical Ltd.
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

'''XDG BaseDirectory abstraction for non-Linux platforms.'''
import os
import sys

class NotSupportedError(Exception):
    '''Unsupported platform version.'''

try:
    from xdg.BaseDirectory import xdg_config_home, xdg_cache_home
except ImportError:
    if sys.platform == 'win32':
        from bzrlib import win32utils as win
        xdg_config_home = win.get_appdata_location_unicode()
        xdg_cache_home = get_temp_location()


# XXX This function should be merged into bzrlib.win32utils
def get_temp_location():
    '''Return temporary (cache) directory'''
    if sys.platform == 'win32':
        # Doing good
        temp = os.environ.get('TEMP')
        if temp:
            return temp

        # Not on Vista/XP/2000
        windir = os.environ.get('windir')
        if windir:
            temp = os.path.join(windir, 'Temp')
            if os.path.isdir(temp):
                return temp

    # Not on win32 or nothing found
    return None
