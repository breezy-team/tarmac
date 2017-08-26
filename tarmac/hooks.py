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

import logging

from breezy import hooks


class TarmacHookRegistry(hooks.Hooks):
    '''Hooks for Tarmac.'''

    def __init__(self):
        hooks.Hooks.__init__(self)

        self.logger = logging.getLogger('tarmac')
        self._hooks = [
            ('tarmac_pre_commit',
             'Called right after Tarmac checks out and merges in a new '
             'branch, but before committing.',
             (0, 2), False),
            ('tarmac_post_commit',
             'Called right after Tarmac commits the merged revision',
             (0, 2), False),
            ('tarmac_pre_merge',
             'Called right before tarmac begins attempting to merge '
             'approved branches into the target branch.',
             (0, 3, 3), False),
            ('tarmac_post_merge',
             'Called right after Tarmac finishes merging approved '
             'branches into the target branch.',
             (0, 3, 3), False),
            ]
        for hook in self._hooks:
            name, doc, added, deprecated = hook
            try:
                self.add_hook(name, doc, added, deprecated=deprecated)
            except AttributeError:
                self.logger.warn(
                    'Using deprecated breezy API. You should upgrade to '
                    'a newer release of bzr.')
                self.create_hook(hooks.HookPoint(name, doc, added, deprecated))

    def fire(self, hook_name, *args, **kwargs):
        """Fire all registered hooks for hook_name.

        This implements a way to fire the hook, which breezy.hooks.Hooks
        doesn't have. If this turns out to be helpful, than a patch to Bazaar
        should be made to implement it in Bazaar.
        """
        hook_point = self[hook_name]
        for callback in hook_point:
            callback(*args, **kwargs)


tarmac_hooks = TarmacHookRegistry()
