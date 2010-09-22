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
from tarmac.tests.mock import Thing


class BugResolverTests(TarmacTestCase):
    """Test the BugResolver."""

    def setUp(self):
        """Set up data for the tests."""
        super(BugResolverTests, self).setUp()
        self.proposal = Thing()
        self.plugin = BugResolver()
        self.projects = [Thing(name='target',
                               series='stable',
                               getSeries=self.getSeries),
                         Thing(name='target',
                               series='trunk',
                               getSeries=self.getSeries),
                         Thing(name='ubuntu',
                               series='badger',
                               getSeries=self.getSeries)]
        self.targets = [Thing(name='target'),
                        Thing(name='target/stable'),
                        Thing(name='target (Ubuntu Badger)')]
        self.bugs = {'0': Thing(
                bug_tasks=[Thing(target=self.targets[0], status='In Progress',
                                 lp_save=self.lp_save),
                           Thing(target=self.targets[2], status='Incomplete',
                                 lp_save=self.lp_save)]),
                     '1': Thing(
                bug_tasks=[Thing(target=self.targets[1], status='Confirmed',
                                 lp_save=self.lp_save)])}

    def getSeries(self, name=None):
        """Faux getSeries for testing."""
        try:
            return [x for x in self.projects if x.series == name][0]
        except IndexError:
            return None

    def lp_save(self, *args, **kwargs):
        """Dummy lp_save method."""
        pass

    def test_run(self):
        """Test that the plug-in runs correctly."""
        target = Thing(fixed_bugs=self.bugs.keys(),
                       project=self.projects[1],
                       lp_branch=Thing(project=self.projects[1],
                                       bzr_identity='lp:target'))
        launchpad = Thing(bugs=self.bugs)
        command = Thing(launchpad=launchpad)
        self.plugin.run(command=command, target=target, source=None,
                        proposal=self.proposal)
        self.assertEqual(self.bugs['0'].bug_tasks[0].status, u'Fix Committed')
        self.assertEqual(self.bugs['0'].bug_tasks[1].status, u'Incomplete')
        self.assertEqual(self.bugs['1'].bug_tasks[0].status, u'Confirmed')

    def test_run_with_series(self):
        """Test that bug resolution for series on bugs works."""
        target = Thing(fixed_bugs=self.bugs.keys(),
                       project=self.projects[1],
                       lp_branch=Thing(project=self.projects[1],
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
                       project=self.projects[1],
                       lp_branch=Thing(project=self.projects[1],
                                       bzr_identity='lp:target/invalid'))
        launchpad = Thing(bugs=self.bugs)
        command = Thing(launchpad=launchpad)
        self.plugin.run(command=command, target=target, source=None,
                        proposal=self.proposal)
        self.assertEqual(self.bugs['0'].bug_tasks[0].status, u'In Progress')
        self.assertEqual(self.bugs['0'].bug_tasks[1].status, u'Incomplete')
        self.assertEqual(self.bugs['1'].bug_tasks[0].status, u'Confirmed')
