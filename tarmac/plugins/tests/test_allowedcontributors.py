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
"""Tests for the Allowed Contributors plug-in."""

from tarmac.plugins.allowedcontributors import (
    InvalidContributor, AllowedContributors)
from tarmac.tests import TarmacTestCase
from tarmac.tests.mock import Thing


class AllowedContributorTests(TarmacTestCase):
    """Test the contributor validation."""

    def setUp(self):
        """Set up data for the tests."""
        super(AllowedContributorTests, self).setUp()
        self.proposal = Thing(source_branch=Thing(display_name=u'lp:source'),
                              target_branch=Thing(display_name=u'lp:target'))
        self.plugin = AllowedContributors()
        people = {u'person1': Thing(name=u'person1',
                                    getMembersByStatus=self.noMembersByStatus),
                  u'person2': Thing(name=u'person2',
                                    getMembersByStatus=self.noMembersByStatus),
                  u'person3': Thing(name=u'person3',
                                    getMembersByStatus=self.noMembersByStatus),
                  u'team1': Thing(name=u'team1',
                                  getMembersByStatus=self.getMembersByStatus),
                  }
        self.people = people

    def getMembersByStatus(self, status=None):
        """Fake method to return some team members."""
        members = [Thing(name=u'person1', status=u'Administrator'),
                   Thing(name=u'person3', status=u'Approved'),
                   Thing(name=u'person8', status=u'Invited'),
                   Thing(name=u'personX', status=u'Expired')]
        return [x for x in members if x.status in status]

    def noMembersByStatus(self, status=None):
        """Fake method to not return any members for people."""
        return []

    def test_run(self):
        """Test that the plug-in runs correctly."""
        config = Thing(allowed_contributors=u'person2,team1')
        source = Thing(authors=[u'person1', u'person2', u'person3'])
        target = Thing(config=config)
        launchpad = Thing(people=self.people)
        command = Thing(launchpad=launchpad)
        self.plugin.run(command=command, target=target, source=source,
                        proposal=self.proposal)

    def test_run_failure(self):
        """Test that the plug-in fails correctly."""
        config = Thing(allowed_contributors=u'team1')
        source = Thing(authors=[u'person1', u'person2', u'person3'])
        target = Thing(config=config)
        launchpad = Thing(people=self.people)
        command = Thing(launchpad=launchpad)
        self.assertRaises(InvalidContributor,
                          self.plugin.run,
                          command=command, target=target, source=source,
                          proposal=self.proposal)
