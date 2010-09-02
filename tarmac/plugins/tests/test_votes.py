"""Tests for the votes plugin."""

import operator

from tarmac.plugins.votes import Votes
from tarmac.tests import TarmacTestCase


class thing(object):
    """Quickly create an object with given attributes."""
    def __init__(self, **names):
        self.__dict__.update(names)


class TestVotes(TarmacTestCase):

    def setUp(self):
        super(TestVotes, self).setUp()
        self.proposal = thing(
            source_branch=thing(
                owner=thing(display_name="Arthur Author", name="arthur"),
                linked_bugs=[thing(id=1234), thing(id=5678)]),
            commit_message="Awesome",
            reviewer=thing(display_name="Randy Reviewer"),
            votes=[
                thing(
                    comment=thing(vote=u"Approve"),
                    reviewer=thing(
                        display_name="Virgil Voter", name="virgil")),
                thing(
                    comment=thing(vote=u"Approve"),
                    reviewer=thing(
                        display_name="Virginia Voter", name="virginia")),
                thing(
                    comment=thing(vote=u"Abstain"),
                    reviewer=thing(
                        display_name="Virginia Voter", name="virginia")),
                thing(
                    comment=thing(vote=u"Needs Information"),
                    reviewer=thing(
                        display_name="Virginia Voter", name="virginia")),
                ])
        self.votes = Votes()

    def test_count_votes(self):
        expected = {u"Approve": 2, u"Needs Information": 1, u"Abstain": 1}
        observed = self.votes.count_votes(self.proposal)
        self.assertEqual(expected, observed)

    def test_parse_criteria(self):
        expected = [
            (u"Approve", operator.ge, 2),
            (u"Disapprove", operator.eq, 0),
            ]
        observed = self.votes.parse_criteria(
            "  Approve >= 2, Disapprove == 0; noise")
        self.assertEqual(expected, list(observed))

    def test_evaluate_criteria(self):
        self.assertTrue(
            self.votes.evaluate_criteria(
                {"Approve": 3}, [(u"Approve", operator.ge, 2)]))
        self.assertFalse(
            self.votes.evaluate_criteria(
                {"Approve": 3}, [(u"Approve", operator.lt, 3)]))
        self.assertFalse(
            self.votes.evaluate_criteria(
                {"Approve": 2, "Disapprove": 1},
                [(u"Approve", operator.ge, 3),
                 (u"Disapprove", operator.eq, 0)]))
