# Copyright 2010 Canonical, Ltd.
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
"""Tests for the BugResolver plug-in."""

from tarmac.plugins.bugresolver import BugResolver
from tarmac.tests import TarmacTestCase
from tarmac.tests import Thing
from datetime import datetime, timedelta
from mock import MagicMock


class BugResolverTests(TarmacTestCase):
    """Test the BugResolver."""

    def setUp(self):
        """Set up data for the tests."""
        super(BugResolverTests, self).setUp()
        self.proposal = Thing()
        self.plugin = BugResolver()
        self.plugin.config = {
            "set_milestone": "False",
            "default_milestone": None}
        self.milestone_untargeted_a = Thing(name="a", date_targeted=None)
        self.milestone_past = Thing(
            name="past",
            date_targeted=datetime.utcnow() - timedelta(weeks=2))
        self.milestone_future = Thing(
            name="future",
            date_targeted=datetime.utcnow() + timedelta(weeks=2))
        self.milestone_far_future = Thing(
            name="far_future",
            date_targeted=datetime.utcnow() + timedelta(weeks=6))
        self.milestone_untargeted_b = Thing(name="b", date_targeted=None)
        self.milestone_untargeted_c = Thing(name="c", date_targeted=None)
        self.milestone_with_bug = Thing(
            name="with_bug",
            date_targeted=datetime.utcnow() - timedelta(weeks=2),
            bug=Thing(id=12345), bug_target_name="foo_project")
        self.series = [Thing(name='trunk'),
                       Thing(name='stable')]
        self.projects = [Thing(name='target',
                               development_focus=self.series[0],
                               getSeries=self.getSeries),
                         Thing(name='ubuntu',
                               development_focus=Thing(name=u'coelecanth'),
                               getSeries=self.getSeries)]
        self.targets = self.series + [Thing(name=u'target (Ubuntu Badger)')]
        self.targets[0] = self.projects[0]
        self.bugs = {'0': Thing(
                bug_tasks=[Thing(target=self.targets[0], status=u'In Progress',
                                 lp_save=self.lp_save, milestone=None,
                                 bug=Thing(id="0"),
                                 bug_target_name=self.targets[0].name),
                           Thing(target=self.targets[2], status=u'Incomplete',
                                 lp_save=self.lp_save, milestone=None,
                                 bug=Thing(id="0"),
                                 bug_target_name=self.targets[2].name)]),
                     '1': Thing(
                bug_tasks=[Thing(target=self.targets[1], status=u'Confirmed',
                                 lp_save=self.lp_save,
                                 milestone=self.milestone_with_bug,
                                 bug=Thing(id="1"),
                                 bug_target_name=self.targets[2].name)])}
        self.now = datetime.utcnow()
        # Insert out of order to make sure they sort correctly.
        self.milestones = [
                self.milestone_far_future, self.milestone_with_bug,
                self.milestone_past, self.milestone_future]
        self.milestones_extended = [
                self.milestone_untargeted_c, self.milestone_untargeted_b,
                self.milestone_untargeted_a]
        self.milestones_extended.extend(self.milestones)
        self.projects[0].active_milestones = self.milestones
        self.projects[1].active_milestones = self.milestones_extended

    def getSeries(self, name=None):
        """Faux getSeries for testing."""
        try:
            return [x for x in self.series if x.name == name][0]
        except IndexError:
            return None

    def lp_save(self, *args, **kwargs):
        """Dummy lp_save method."""
        pass

    def test_run(self):
        """Test that the plug-in runs correctly."""
        target = Thing(fixed_bugs=self.bugs.keys(),
                       lp_branch=Thing(project=self.projects[0],
                                       bzr_identity='lp:target'))
        launchpad = Thing(bugs=self.bugs)
        command = Thing(launchpad=launchpad)
        self.plugin.run(command=command, target=target, source=None,
                        proposal=self.proposal)
        self.assertEqual(self.bugs['0'].bug_tasks[0].status, u'Fix Committed')
        self.assertEqual(self.bugs['0'].bug_tasks[1].status, u'Incomplete')
        self.assertEqual(self.bugs['1'].bug_tasks[0].status, u'Confirmed')

    def test_run_with_set_milestone(self):
        """Test plug-in with the set_milestone setting runs correctly."""
        target = Thing(fixed_bugs=self.bugs.keys(),
                       lp_branch=Thing(project=self.projects[0],
                                       bzr_identity='lp:target'),
                       config=Thing(set_milestone="true"))
        launchpad = Thing(bugs=self.bugs)
        command = Thing(launchpad=launchpad)
        self.plugin.run(command=command, target=target, source=None,
                            proposal=self.proposal)
        self.assertEqual(self.bugs['0'].bug_tasks[0].milestone,
                         self.milestone_future)
        self.assertEqual(self.bugs['0'].bug_tasks[1].milestone, None)
        self.assertEqual(self.bugs['1'].bug_tasks[0].milestone,
                         self.milestone_with_bug)

    def test_run_with_no_bugs(self):
        """Test that bug resolution for no bugs does nothing."""
        target = Thing(fixed_bugs=None,
                       lp_branch=Thing(project=self.projects[0],
                                       bzr_identity='lp:target/stable'))
        launchpad = Thing(bugs=self.bugs)
        command = Thing(launchpad=launchpad)
        self.plugin.run(command=command, target=target, source=None,
                        proposal=self.proposal)
        self.assertEqual(self.bugs['0'].bug_tasks[0].status, u'In Progress')
        self.assertEqual(self.bugs['0'].bug_tasks[1].status, u'Incomplete')
        self.assertEqual(self.bugs['1'].bug_tasks[0].status, u'Confirmed')

    def test_run_with_series(self):
        """Test that bug resolution for series on bugs works."""
        target = Thing(fixed_bugs=self.bugs.keys(),
                       lp_branch=Thing(project=self.projects[0],
                                       bzr_identity='lp:target/stable'))
        launchpad = Thing(bugs=self.bugs)
        command = Thing(launchpad=launchpad)
        self.plugin.run(command=command, target=target, source=None,
                        proposal=self.proposal)
        self.assertEqual(self.bugs['0'].bug_tasks[0].status, u'In Progress')
        self.assertEqual(self.bugs['0'].bug_tasks[1].status, u'Incomplete')
        self.assertEqual(self.bugs['1'].bug_tasks[0].status, u'Fix Committed')

    def test_run_with_series_invalid(self):
        """Test that bug resolution for series on bugs works."""
        target = Thing(fixed_bugs=self.bugs.keys(),
                       lp_branch=Thing(project=self.projects[0],
                                       bzr_identity='lp:target/invalid'))
        launchpad = Thing(bugs=self.bugs)
        command = Thing(launchpad=launchpad)
        self.plugin.run(command=command, target=target, source=None,
                        proposal=self.proposal)
        self.assertEqual(self.bugs['0'].bug_tasks[0].status, u'In Progress')
        self.assertEqual(self.bugs['0'].bug_tasks[1].status, u'Incomplete')
        self.assertEqual(self.bugs['1'].bug_tasks[0].status, u'Confirmed')

    def test__find_target_milestone_older(self):
        """Dates before all milestones return the oldest milestone."""
        milestone = self.plugin._find_target_milestone(
            self.projects[0],
            self.milestone_past.date_targeted - timedelta(weeks=1))
        self.assertEqual(milestone, self.milestone_past)

    def test__find_target_milestone_between(self):
        """Test that dates between milestones return the closest newest."""
        milestone = self.plugin._find_target_milestone(
            self.projects[0],
            self.milestone_past.date_targeted + timedelta(weeks=1))
        self.assertEqual(milestone, self.milestone_future)

    def test__find_target_milestone_newer(self):
        """Test that dates after milestones return the newest."""
        milestone = self.plugin._find_target_milestone(
            self.projects[0],
            self.milestone_far_future.date_targeted + timedelta(weeks=1))
        self.assertEqual(milestone, self.milestone_far_future)

    def test__find_target_milestone_newer_no_expected_date(self):
        """Dates after milestones return the least sorted no-expected-date."""
        milestone = self.plugin._find_target_milestone(
            self.projects[1],
            self.milestone_far_future.date_targeted + timedelta(weeks=1))
        self.assertEqual(milestone, self.milestone_untargeted_a)

    def test__find_target_milestone_with_default(self):
        """Test that specifying a default gets a specific milestone."""
        self.projects[0].active_milestones = self.milestones_extended
        self.plugin.config["default_milestone"] = "c"
        milestone = self.plugin._find_target_milestone(
            self.projects[0],
            self.milestone_far_future.date_targeted + timedelta(weeks=1))
        self.assertEqual(milestone, self.milestone_untargeted_c)

    def test__find_milestone_positive(self):
        """Given a project, the list of milestones is returned."""
        milestones = self.plugin._find_milestones(self.projects[0])
        self.assertEqual(len(milestones), 4)

    def test__find_milestone_negative(self):
        """Given a project with no milestones, _find_milestone handles it"""
        milestones = self.plugin._find_milestones(Thing(active_milestones=[]))
        self.assertEqual(len(milestones), 0)

    def test__find_milestone_specific_negative(self):
        """Find a secific milestone that isn't there, check for log"""
        self.plugin.logger.warning = MagicMock()
        self.plugin.config["default_milestone"] = "FOO"
        milestones = self.plugin._find_milestones(self.projects[0])
        self.assertEqual(len(milestones), 0)
        self.assertEqual(self.plugin.logger.warning.call_count, 1)

    def test__find_milestone_no_dates(self):
        """Find a specific milestones without a targeted date"""
        self.plugin.config["default_milestone"] = "b"
        milestones = self.plugin._find_milestones(self.projects[1])
        self.assertEqual(len(milestones), 1)
        self.assertEqual(milestones[0], self.milestone_untargeted_b)

    def test__get_and_parse_config_set_milestone_true_upper(self):
        """Test config parsing - set_milestone: True."""
        config = self.plugin._get_and_parse_config(
                Thing(config=Thing(set_milestone="True")))
        self.assertEqual(config["set_milestone"], True)

    def test__get_and_parse_config_set_milestone_one(self):
        """Test config parsing - set_milestone: 1."""
        config = self.plugin._get_and_parse_config(
                Thing(config=Thing(set_milestone="1")))
        self.assertEqual(config["set_milestone"], True)

    def test__get_and_parse_config_set_milestone_true_lower(self):
        """Test config parsing - set_milestone: true."""
        config = self.plugin._get_and_parse_config(
                Thing(config=Thing(set_milestone="true")))
        self.assertEqual(config["set_milestone"], True)

    def test__get_and_parse_config_default_milestone_A(self):
        """Test config parsing - default_milestone: A."""
        config = self.plugin._get_and_parse_config(
                Thing(config=Thing(default_milestone="A")))
        self.assertEqual(config["default_milestone"], "A")

    def test__get_and_parse_config_default_milestone_none(self):
        """Test config parsing - default_milestone: ."""
        config = self.plugin._get_and_parse_config(
                Thing(config=Thing(default_milestone="")))
        self.assertEqual(config["default_milestone"], None)

    def test__get_and_parse_config_default_milestone_default(self):
        """Test config parsing - defaults."""
        config = self.plugin._get_and_parse_config(
                Thing(config=Thing()))
        self.assertEqual(config["set_milestone"], False)
        self.assertEqual(config["default_milestone"], None)

    def test__set_milestone_on_task_config_not_set(self):
        """config option not set, no-op"""
        self.plugin.logger.info = MagicMock()
        self.plugin.logger.warning = MagicMock()
        self.plugin.config = {
            "set_milestone": False, "default_milestone": None}
        self.plugin._set_milestone_on_task(
            self.projects[0], self.bugs['0'].bug_tasks[0])
        self.assertEqual(self.bugs['0'].bug_tasks[0].milestone, None)
        self.assertEqual(self.plugin.logger.info.call_count, 0)
        self.assertEqual(self.plugin.logger.warning.call_count, 0)

    def test__set_milestone_on_task_milestone_already_set(self):
        """milestone is already set, should leave task untouched"""
        self.plugin.logger.info = MagicMock()
        self.plugin.config = {"set_milestone": True, "default_milestone": "past"}
        self.plugin._set_milestone_on_task(
            self.projects[0], self.bugs['1'].bug_tasks[0])
        self.assertEqual(
            self.bugs['1'].bug_tasks[0].milestone, self.milestone_with_bug)
        self.assertIn("already has milestone",
                      self.plugin.logger.info.call_args[0][0])

    def test__set_milestone_on_task_config_set(self):
        """config option set, milestone is being set, action logged"""
        self.plugin.logger.info = MagicMock()
        self.plugin.config = {"set_milestone": True, "default_milestone": None}
        self.plugin._set_milestone_on_task(
            self.projects[0], self.bugs['0'].bug_tasks[0])
        self.assertEqual(
            self.bugs['0'].bug_tasks[0].milestone, self.milestone_future)
        self.assertEqual(self.plugin.logger.info.call_count, 1)
