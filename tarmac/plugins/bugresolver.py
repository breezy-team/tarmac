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
from datetime import datetime


class BugResolver(TarmacPlugin):
    """Tarmac plug-in for resolving a bug."""

    def run(self, command, target, source, proposal):
        """Mark bugs fixed in the bug tracker."""
        fixed_bugs = target.fixed_bugs
        if not fixed_bugs:
            return

        # Retrieve configuration
        self.config = self._get_and_parse_config(target, command)

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
                task.status = 'Fix Committed'
                self._set_milestone_on_task(project, task)
                task.lp_save()
            else:
                self.logger.info('Target %s/%s not found in bug #%s.',
                                 project.name, series.name, bug_id)

    def _get_and_parse_config(self, *args):
        """
        Retrieve and parse configuration settings for this plugin.
        Return as a dict structure.
        """
        set_milestone = self.get_config("set_milestone", "False", *args)
        if set_milestone.lower() == "true" or set_milestone == "1":
            set_milestone = True
        else:
            set_milestone = False

        default_milestone = self.get_config("default_milestone", None, *args)
        if default_milestone == "":
            default_milestone = None

        return {
            "set_milestone": set_milestone,
            "default_milestone": default_milestone}

    def _set_milestone_on_task(self, project, task):
        """
        Attempt to auto-determine the milestone to set, and set the milestone
        of the given task.  If the task already has a milestone set => noop.
        Only processed if config setting `set_milestone` == True.
        """
        if not self.config["set_milestone"]:
            return
        task_milestone = task.milestone
        if task_milestone is not None:
            self.logger.info(
                "Task: %s/%s already has milestone: %s set, skipping" % (
                    task.bug.id, task.bug_target_name, task_milestone.name))
            return
        now = datetime.utcnow()
        target_milestone = self._find_target_milestone(project, now)
        self.logger.info("%s/%s: Setting Milestone: %s",
                task.bug.id, task.bug_target_name, target_milestone)
        task.milestone = target_milestone

    def _find_milestones(self, project):
        """
        Return list of active milestones in a project.  If the config
        `default_milestone` is set filter by that.  If not found, an 
        empty list will be returned.
        """
        default = self.config["default_milestone"]
        if default is None:
            return list(project.active_milestones)
        for milestone in project.active_milestones:
            if milestone.name == default:
                return [milestone]
        self.logger.warning("Default Milestone not found: %s" % default)
        return []

    def _find_target_milestone(self, project, now):
        """
        Find a target milestone when resolving a bug task.

        Compare the selected datetime `now` to the list of milestones.
        Return the milestone where `targeted_date` is newer than the given
        datetime.  If the given time is greater than all open milestones:
        target to the newest milestone in the list.

        In this algorithm, milestones without targeted dates appear lexically
        sorted at the end of the list.  So the lowest sorting one will get
        chosen if all milestones with dates attached are exhausted.

        In other words, pick one of the milestones for the target.  Preference:
            1) closest milestone (by date) in the future
            2) least lexically sorting milestone (by name)
            3) the last milestone in the list (covers len()==1 case).
        """
        milestones = self._find_milestones(project)
        earliest_after = latest_before = untargeted = None
        for milestone in milestones:
            if milestone.date_targeted is None:
                if untargeted is not None:
                    if milestone.name < untargeted.name:
                        untargeted = milestone
                else:
                    untargeted = milestone
            elif milestone.date_targeted > now:
                if earliest_after is not None:
                    if earliest_after.date_targeted > milestone.date_targeted:
                        earliest_after = milestone
                else:
                    earliest_after = milestone
            elif milestone.date_targeted < now:
                if latest_before is not None:
                    if latest_before.date_targeted < milestone.date_targeted:
                        latest_before = milestone
                else:
                    latest_before = milestone

        if earliest_after is not None:
            return earliest_after
        elif untargeted is not None:
            return untargeted
        else:
            return latest_before


tarmac_hooks['tarmac_post_commit'].hook(BugResolver(), 'Bug resolver')
