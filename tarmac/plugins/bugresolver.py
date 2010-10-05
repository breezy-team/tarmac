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

        project = target.lp_branch.project
        try:
            series_name = target.lp_branch.bzr_identity.split('/')[1]
        except IndexError:
            series = project.development_focus
        else:
            series = project.getSeries(name=series_name)

        if not series:
            self.logger.info('Target branch has no valid project series.')
            return

        def find_task_for_target(bug, target):
            for task in bug.bug_tasks:
                if task.target == target:
                    return task
            return None

        for bug_id in fixed_bugs:
            bug = command.launchpad.bugs[bug_id]
            task = find_task_for_target(bug, series)
            if not task and series == project.development_focus:
                task = find_task_for_target(bug, project)

            if task:
                task.status = u'Fix Committed'
                task.lp_save()
            else:
                self.logger.info('Target %s/%s not found in bug #%s.',
                                 project.name, series.name, bug_id)


tarmac_hooks['tarmac_post_commit'].hook(BugResolver(), 'Bug resolver')
