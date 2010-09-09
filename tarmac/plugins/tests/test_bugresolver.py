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

    def test_run(self):
        """Test that the plug-in runs correctly."""
        def lp_save(*args, **kwargs):
            """Dummy lp_save method."""
            pass

        bugs = {
            '0' : Thing(
                bug_tasks=[Thing(target='Target', status='In Progress',
                                 lp_save=lp_save),
                           Thing(target='Ubuntu', status='Incomplete',
                                 lp_save=lp_save)]),
            '1' : Thing(
                bug_tasks=[Thing(target='Target', status='Confirmed',
                                 lp_save=lp_save)]),
            }
        target = Thing(fixed_bugs=bugs.keys(),
                       lp_branch=Thing(project='Target'))
        launchpad = Thing(bugs=bugs)
        command = Thing(launchpad=launchpad)
        self.plugin.run(command=command, target=target, source=None,
                        proposal=self.proposal)
        self.assertEqual(bugs['0'].bug_tasks[0].status, u'Fix Committed')
        self.assertEqual(bugs['0'].bug_tasks[1].status, u'Incomplete')
        self.assertEqual(bugs['1'].bug_tasks[0].status, u'Fix Committed')
