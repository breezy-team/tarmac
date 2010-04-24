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

'''Hooks for Tarmac.'''

from bzrlib import hooks


class TarmacHookPoint(hooks.HookPoint):
    '''A special HookPoint for Tarmac.

    This HookPoint implements a fire method that the bzrlib.hooks.HookPoint
    doesn't have.  If this turns out to be helpful, than a patch to Bazaar
    should be made to implement it in Bazaar.
    '''

    def fire(self, *args, **kwargs):
        '''Fire all registered hooks for self.'''
        for hook in self:
            hook(*args, **kwargs)


class TarmacHookRegistry(hooks.Hooks):
    '''Hooks for Tarmac.'''

    def __init__(self):
        hooks.Hooks.__init__(self)

        self.create_hook(TarmacHookPoint('tarmac_pre_commit',
            'Called right after Tarmac checks out and merges in a new '
            'branch, but before committing.',
            (1, 14, 0), False))

        self.create_hook(TarmacHookPoint('tarmac_post_commit',
            'Called right after Tarmac commits the merged revision',
            (1, 14, 0), False))


tarmac_hooks = TarmacHookRegistry()
