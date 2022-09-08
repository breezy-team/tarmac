# Copyright 2010 Canonical Ltd.
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

"""Tests for the votes plugin."""

import operator

from tarmac.plugins.votes import InvalidCriterion, Votes, VotingViolation
from tarmac.tests import TarmacTestCase
from tarmac.tests import Thing


class TestVotes(TarmacTestCase):

    def setUp(self):
        super(TestVotes, self).setUp()
        self.proposal = Thing(
            target_branch=Thing(isPersonTrustedReviewer=self.isReviewer),
            votes=[
                Thing(comment=Thing(vote="Approve"),
                      is_pending=False,
                      reviewer=Thing(display_name='Reviewer')),
                Thing(comment=Thing(vote="Approve"),
                      is_pending=False,
                      reviewer=Thing(display_name='Reviewer')),
                Thing(comment=Thing(vote="Abstain"),
                      is_pending=False,
                      reviewer=Thing(display_name='Reviewer')),
                Thing(comment=Thing(vote="Needs Information"),
                      is_pending=False,
                      reviewer=Thing(display_name='Reviewer')),
                Thing(comment=Thing(vote='Disapprove'),
                      is_pending=False,
                      reviewer=Thing(display_name='Community')),
                ])
        self.plugin = Votes()

    def isReviewer(self, reviewer=None):
        """Is the reviewer a trusted reviewer?"""
        if reviewer.display_name == 'Reviewer':
            return True
        return False

    def test_count_votes(self):
        expected = {"Approve": 2, "Needs Information": 1}
        observed = self.plugin.count_votes(self.proposal)
        self.assertEqual(expected, observed)

    def test_parse_criteria(self):
        expected = [
            ("Approve", operator.ge, 2),
            ("Disapprove", operator.eq, 0),
            ]
        observed = self.plugin.parse_criteria(
            "  Approve >= 2, Disapprove == 0; ")
        self.assertEqual(expected, observed)

    def test_parse_invalid_criteria(self):
        self.assertRaises(
            InvalidCriterion, self.plugin.parse_criteria, "foo")
        self.assertRaises(
            InvalidCriterion, self.plugin.parse_criteria,
            "Approve == 1; Disapprove is 0")

    def test_evaluate_criteria(self):
        self.assertTrue(
            self.plugin.evaluate_criteria(
                {"Approve": 3}, [("Approve", operator.ge, 2)]))
        self.assertFalse(
            self.plugin.evaluate_criteria(
                {"Approve": 3}, [("Approve", operator.lt, 3)]))
        self.assertFalse(
            self.plugin.evaluate_criteria(
                {"Approve": 2, "Disapprove": 1},
                [("Approve", operator.ge, 3),
                 ("Disapprove", operator.eq, 0)]))

    def test_run(self):
        target = Thing(
            config=Thing(
                voting_criteria="Approve >= 2, Disapprove == 0"))
        self.plugin.run(
            command=None, target=target, source=None, proposal=self.proposal)

    def test_run_no_votes(self):
        """Test that all community reviews fails."""
        target = Thing(config=Thing(voting_criteria='Approve == 2'))
        self.proposal.votes = [
            Thing(comment=Thing(vote='Approve'),
                  reviewer=Thing(display_name='Community1')),
            Thing(comment=Thing(vote='Approve'),
                  reviewer=Thing(display_name='Community2'))]
        self.assertEqual({}, self.plugin.count_votes(self.proposal))
        try:
            self.plugin.run(
                command=None, target=target, source=None,
                proposal=self.proposal)
        except VotingViolation as error:
            self.assertEqual(
                ('Voting does not meet specified criteria. '
                 'Required: Approve == 2. '
                 'Got: .'),
                error.comment)
        else:
            self.fail('Votes.run() did not raise VotingViolation.')

    def test_run_failure(self):
        target = Thing(
            config=Thing(
                voting_criteria="Approve >= 2, Needs Information == 0"))
        try:
            self.plugin.run(
                command=None, target=target, source=None,
                proposal=self.proposal)
        except VotingViolation as error:
            self.assertEqual(
                ("Voting does not meet specified criteria. "
                 "Required: Approve >= 2, Needs Information == 0. "
                 "Got: 2 Approve, 1 Needs Information."),
                error.comment)
        else:
            self.fail("Votes.run() did not raise VotingViolation.")

    def test_run_global_config(self):
        target = Thing()
        self.config.set('Tarmac', 'voting_criteria',
                        'Approve >= 2, Disapprove == 0')
        command = Thing(config=self.config)
        self.called = False
        old_count_votes = self.plugin.count_votes

        def count_votes(proposal):
            """OVerride for count_votes to validate it was called."""
            self.called = True
            return old_count_votes(proposal)

        self.plugin.count_votes = count_votes
        self.plugin.run(command=command, target=target,
                        source=None, proposal=self.proposal)
        if not self.called:
            self.fail('No voting_criteria configuration found')

    def test_run_global_config_failure(self):
        target = Thing()
        self.config.set('Tarmac', 'voting_criteria',
                        'Approve >= 2, Needs Information == 0')
        command = Thing(config=self.config)
        try:
            self.plugin.run(
                command=command, target=target, source=None,
                proposal=self.proposal)
        except VotingViolation as error:
            self.assertEqual(
                ("Voting does not meet specified criteria. "
                 "Required: Approve >= 2, Needs Information == 0. "
                 "Got: 2 Approve, 1 Needs Information."),
                error.comment)
        else:
            self.fail("Votes.run() did not raise VotingViolation.")

    def test_count_pending(self):
        """Test that is_pending gets counted as Pending."""
        expected = {"Approve": 1, "Pending": 1}
        self.proposal.votes = [
            Thing(comment=Thing(vote=''),
                  is_pending=True,
                  reviewer=Thing(display_name='Reviewer')),
            Thing(comment=Thing(vote='Approve'),
                  is_pending=False,
                  reviewer=Thing(display_name='Reviewer'))]
        self.assertEqual(expected, self.plugin.count_votes(self.proposal))
