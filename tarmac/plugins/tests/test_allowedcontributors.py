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
    InvalidContributor, InvalidPersonOrTeam, AllowedContributors)
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
        people = Thing(
            person1=Thing(name=u'person1',
                          is_team=False,
                          preferred_email_address=Thing(email=u'person1'),
                          confirmed_email_addresses=Thing()),
            person2=Thing(name=u'person2',
                          is_team=False,
                          preferred_email_address=Thing(email=u'person2'),
                          confirmed_email_addresses=Thing()),
            person3=Thing(name=u'person3',
                          is_team=False,
                          preferred_email_address=Thing(email=u'person3'),
                          confirmed_email_addresses=Thing()),
            team1=Thing(name=u'team1',
                        is_team=True,
                        preferred_email_address=Thing(email=None),
                        confirmed_email_addresses=Thing(),
                        members=None),
            team2=Thing(name=u'team2',
                        is_team=True,
                        preferred_email_address=Thing(email=None),
                        confirmed_email_address=Thing(),
                        members=None),
            getByEmail=self.getByEmail)
        self.people = people
        self.people.team1.members = [self.people.person1, self.people.person3]
        self.people.team2.members = [self.people.team1, self.people.person2]

    def getByEmail(self, email=None):
        """Fake method to return a person based on e-mail address."""
        if email == 'un@register.ed':
            return None
        for person in self.people:
            if person.preferred_email_address.email == email:
                return person
            if email in [y.email for y in person.confirmed_email_addresses]:
                return person

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

    def test_run_private_team(self):
        """Test that the plug-in runs correctly."""
        config = Thing(allowed_contributors=u'private_team')
        source = Thing(authors=[u'person1', u'person2', u'person3'])
        target = Thing(config=config)
        launchpad = Thing(people=self.people)
        command = Thing(launchpad=launchpad)
        self.assertRaises(InvalidPersonOrTeam,
                          self.plugin.run,
                          command=command, target=target, source=source,
                          proposal=self.proposal)

    def test_person_is_in_subteam(self):
        """Test that is_in_team returns True for person in a subteam."""
        self.assertTrue(self.plugin.is_in_team(self.people.person1,
                                               self.people.team2))

    def test_person_not_in_team(self):
        """Test that is_in_team returns False for person not in a team."""
        self.assertFalse(self.plugin.is_in_team(self.people.person2,
                                                self.people.team1))

    def test_email_not_registered(self):
        """Test that unregistered e-mail address doesn't crash."""
        config = Thing(allowed_contributors=u'private_team')
        source = Thing(authors=[u'un@register.ed'])
        target = Thing(config=config)
        launchpad = Thing(people=self.people)
        command = Thing(launchpad=launchpad)
        self.assertRaises(InvalidContributor,
                          self.plugin.run,
                          command=command, target=target, source=source,
                          proposal=self.proposal)
