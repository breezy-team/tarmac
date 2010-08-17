# Copyright 2010 Canonical, Ltd.
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
"""Tarmac plug-in for setting a bug status post-commit."""

from tarmac.hooks import tarmac_hooks
from tarmac.plugins import TarmacPlugin


class BugResolver(TarmacPlugin):
    """Tarmac plug-in for resolving a bug."""

    def run(self, command, target, source, proposal):
        """Mark bugs fixed in the bug tracker."""
        for bug_id in target.fixed_bugs:
            bug = command.launchpad.bugs[bug_id]
            for task in bug.bug_tasks:
                if task.target == target.lp_branch.project:
                    task.status = u'Fix committed'
                    task.lp_save()
                    return
            

tarmac_hooks['tarmac_post_commit'].hook(BugResolver(), 'Bug resolver')
