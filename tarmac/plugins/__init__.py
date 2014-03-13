# Copyright 2009 Paul Hummer
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

'''Tarmac supported plugins.'''
import logging


class TarmacPlugin(object):
    '''Abstract class for Tarmac plugins.'''

    def __init__(self):
        self.logger = logging.getLogger('tarmac')

    def __call__(self, *args, **kwargs):
        self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        '''Run the hook.'''

    def get_config(self, attribute, default, *args):
        '''
        Lookup configuration and return to caller.
        Return value of `default` if not found.  Typically you would call
        in the following manner:

          value = get_config("my_config_setting", None, command, target)

        @param attribute: The attribute to lookup.
        @param default: The default value to use if nothing found.
        @param *args: objects to probe looking for the requested attribute.
        '''
        for obj in args:
            if hasattr(obj, "config"):
                if hasattr(obj.config, attribute):
                    return getattr(obj.config, attribute)
        return default
