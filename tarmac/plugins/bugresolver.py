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
        fixed_bugs = target.fixed_bugs
        if not fixed_bugs:
            return

        project = target.lp_branch.project.name
        try:
            series = target.lp_branch.bzr_identity.split('/')[1]
        except IndexError:
            series = u'trunk'

        lp_series = target.lp_branch.project.getSeries(name=series)
        if not lp_series:
            self.logger.info('Target branch has no valid project series.')
            return

        for bug_id in fixed_bugs:
            bug = command.launchpad.bugs[bug_id]
            for task in bug.bug_tasks:
                bug_series = None
                try:
                    bug_project = task.target.name.split('/')[0]
                    bug_series = task.target.name.split('/')[1]
                except IndexError:
                    bug_project = task.target.name

                if not bug_series:
                    bug_series = u'trunk'

                if bug_project != project:
                    continue

                if bug_series != series:
                    continue

                task.status = u'Fix Committed'
                task.lp_save()


tarmac_hooks['tarmac_post_commit'].hook(BugResolver(), 'Bug resolver')
