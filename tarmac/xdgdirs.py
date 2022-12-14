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

__all__ = [
    'xdg_cache_home',
    'xdg_config_home',
    ]

import os
import sys


# XXX This function should be merged into breezy.win32utils
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


try:
    import xdg.BaseDirectory
except ImportError:
    if sys.platform == 'win32':
        from breezy import win32utils as win
        xdg_config_home = win.get_appdata_location_unicode()
        xdg_cache_home = get_temp_location()
    else:
        home = os.environ.get('HOME')
        xdg_config_home = os.path.join(home, '.config/')
        xdg_cache_home = os.path.join(home, '.cache/')
else:
    xdg_config_home = xdg.BaseDirectory.xdg_config_home
    xdg_cache_home = xdg.BaseDirectory.xdg_cache_home
