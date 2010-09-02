"""Tests for the votes plugin."""

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
