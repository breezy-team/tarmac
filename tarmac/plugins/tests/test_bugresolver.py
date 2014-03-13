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
        self.milestone1 = Thing(
            name="1", is_active=True,
            date_targeted=datetime.utcnow() - timedelta(weeks=2))
        self.milestone2 = Thing(
            name="2", is_active=True,
            date_targeted=datetime.utcnow() + timedelta(weeks=2))
        self.milestone3 = Thing(
            name="3", is_active=True,
            date_targeted=datetime.utcnow() + timedelta(weeks=6))
        self.milestone4 = Thing(
            name="4", is_active=True,
            date_targeted=None)
        self.milestone5 = Thing(
            name="5", is_active=True,
            date_targeted=None)
        self.milestone6 = Thing(
            name="6", is_active=False,
            date_targeted=datetime.utcnow() + timedelta(weeks=2),
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
                                 lp_save=self.lp_save, milestone=self.milestone6,
                                 bug=Thing(id="1"),
                                 bug_target_name=self.targets[2].name)])}
        self.now = datetime.utcnow()
        # Insert out of order to make sure they sort correctly.
        self.milestones = [
                self.milestone3, self.milestone6, self.milestone1,
                self.milestone2]
        self.milestones_extended = [self.milestone5, self.milestone4]
        self.milestones_extended.extend(self.milestones)
        self.projects[0].all_milestones = self.milestones
        self.projects[1].all_milestones = []

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
                                       bzr_identity='lp:target'),
                       set_milestone="true")
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
                       set_milestone="true")
        all_bugs = self.bugs
        launchpad = Thing(bugs=all_bugs)
        command = Thing(launchpad=launchpad)
        self.plugin.run(command=command, target=target, source=None,
                            proposal=self.proposal)
        self.assertEqual(self.bugs['0'].bug_tasks[0].milestone, self.milestone2)
        self.assertEqual(self.bugs['0'].bug_tasks[1].milestone, None)
        self.assertEqual(self.bugs['1'].bug_tasks[0].milestone, self.milestone6)

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
        """Test that dates before milestones return the oldest."""
        milestone = self.plugin._find_target_milestone(
            self.projects[0],
            self.milestone1.date_targeted - timedelta(weeks=1))
        self.assertEqual(milestone, self.milestone1)

    def test__find_target_milestone_between(self):
        """Test that dates between milestones return the closest newest."""
        milestone = self.plugin._find_target_milestone(
            self.projects[0],
            self.milestone1.date_targeted + timedelta(weeks=1))
        self.assertEqual(milestone, self.milestone2)

    def test__find_target_milestone_newer(self):
        """Test that dates after milestones return the newest."""
        milestone = self.plugin._find_target_milestone(
            self.projects[0], self.milestone3.date_targeted + timedelta(weeks=1))
        self.assertEqual(milestone, self.milestone3)

    def test__find_target_milestone_newer_no_expected_date(self):
        """Test that dates after milestones return the least sorted no-expected-date."""
        self.projects[0].all_milestones = self.milestones_extended
        milestone = self.plugin._find_target_milestone(
            self.projects[0], self.milestone3.date_targeted + timedelta(weeks=1))
        self.assertEqual(milestone, self.milestone4)

    def test__find_target_milestone_with_default(self):
        """Test that specifying a default gets a specific milestone."""
        self.projects[0].all_milestones = self.milestones_extended
        self.plugin.config["default_milestone"] = "6"
        milestone = self.plugin._find_target_milestone(
            self.projects[0], self.milestone3.date_targeted + timedelta(weeks=1))
        self.assertEqual(milestone, self.milestone6)
        self.plugin.config["default_milestone"] = "5"
        milestone = self.plugin._find_target_milestone(
            self.projects[0], self.milestone3.date_targeted + timedelta(weeks=1))
        self.assertEqual(milestone, self.milestone5)

    def test__find_milestone(self):
        """Test that given a project, the list of milestones is returned."""
        self.plugin.logger.warning = MagicMock()
        milestones = self.plugin._find_milestones(self.projects[0])
        self.assertEqual(len(milestones), 3)
        milestones = self.plugin._find_milestones(self.projects[1])
        self.assertEqual(len(milestones), 0)

        # Search for a specific milestone that isn't there (this triggers the
        # warning log)
        self.plugin.config["default_milestone"] = "FOO"
        milestones = self.plugin._find_milestones(self.projects[0])
        self.assertEqual(len(milestones), 0)

        # Add in the milestones with no dates, and make sure I can search
        # for something specific.
        self.projects[0].all_milestones = self.milestones_extended
        self.plugin.config["default_milestone"] = "5"
        milestones = self.plugin._find_milestones(self.projects[0])
        self.assertEqual(len(milestones), 1)
        self.assertEqual(milestones[0], self.milestone5)

        # Make sure warning log was only called once.
        self.assertEqual(self.plugin.logger.warning.call_count, 1)

    def test_get_and_parse_config(self):
        """Test config parsing."""
        config = self.plugin.get_and_parse_config(Thing(set_milestone="True"))
        self.assertEqual(config["set_milestone"], True)
        config = self.plugin.get_and_parse_config(Thing(set_milestone="1"))
        self.assertEqual(config["set_milestone"], True)
        config = self.plugin.get_and_parse_config(Thing(set_milestone="true"))
        self.assertEqual(config["set_milestone"], True)
        config = self.plugin.get_and_parse_config(Thing(default_milestone="A"))
        self.assertEqual(config["default_milestone"], "A")
        config = self.plugin.get_and_parse_config(Thing(default_milestone=""))
        self.assertEqual(config["default_milestone"], None)
