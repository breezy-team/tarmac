"""Tests for the votes plugin."""

import operator

from tarmac.plugins.votes import InvalidCriterion, Votes, VotingViolation
from tarmac.tests import TarmacTestCase


class thing(object):
    """Quickly create an object with given attributes."""
    def __init__(self, **names):
        self.__dict__.update(names)


class TestVotes(TarmacTestCase):

    def setUp(self):
        super(TestVotes, self).setUp()
        self.proposal = thing(
            votes=[
                thing(comment=thing(vote=u"Approve")),
                thing(comment=thing(vote=u"Approve")),
                thing(comment=thing(vote=u"Abstain")),
                thing(comment=thing(vote=u"Needs Information")),
                ])
        self.plugin = Votes()

    def test_count_votes(self):
        expected = {u"Approve": 2, u"Needs Information": 1, u"Abstain": 1}
        observed = self.plugin.count_votes(self.proposal.votes)
        self.assertEqual(expected, observed)

    def test_parse_criteria(self):
        expected = [
            (u"Approve", operator.ge, 2),
            (u"Disapprove", operator.eq, 0),
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
                {"Approve": 3}, [(u"Approve", operator.ge, 2)]))
        self.assertFalse(
            self.plugin.evaluate_criteria(
                {"Approve": 3}, [(u"Approve", operator.lt, 3)]))
        self.assertFalse(
            self.plugin.evaluate_criteria(
                {"Approve": 2, "Disapprove": 1},
                [(u"Approve", operator.ge, 3),
                 (u"Disapprove", operator.eq, 0)]))

    def test_run(self):
        target = thing(
            config=thing(
                voting_criteria="Approve >= 2, Disapprove == 0"))
        self.plugin.run(
            command=None, target=target, source=None, proposal=self.proposal)

    def test_run_failure(self):
        target = thing(
            config=thing(
                voting_criteria="Approve >= 2, Needs Information == 0"))
        try:
            self.plugin.run(
                command=None, target=target, source=None,
                proposal=self.proposal)
        except VotingViolation, error:
            self.assertEqual(
                ("Voting does not meet specified criteria. "
                 "Required: Approve >= 2, Needs Information == 0. "
                 "Got: 1 Abstain, 2 Approve, 1 Needs Information."),
                str(error))
        else:
            raise AssertionError(
                "Votes.run() did not raise VotingViolation.")
