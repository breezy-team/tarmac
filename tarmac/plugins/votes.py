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

"""Tarmac plugin for enforcing a configurable set of voting criteria."""

import operator
import re

from tarmac.exceptions import TarmacMergeError
from tarmac.hooks import tarmac_hooks
from tarmac.plugins import TarmacPlugin


operator_map = {
    "==": operator.eq,
    "<": operator.lt,
    "<=": operator.le,
    ">=": operator.ge,
    ">": operator.gt,
    }

operator_map_inverse = dict(
    (op, name) for (name, op) in operator_map.iteritems())

criteria_split = re.compile(
    "\s* [,;] \s*", re.VERBOSE | re.MULTILINE)

criteria_expr = re.compile(
    r"^ \s* ([a-zA-Z ]+?) \s* (%s) \s* ([0-9]+) \s* $" % (
        "|".join(re.escape(op) for op in operator_map)),
    re.VERBOSE | re.MULTILINE)


class InvalidCriterion(Exception):
    """A voting criterion is not understood."""


class VotingViolation(TarmacMergeError):
    """The voting criteria have not been met."""


class VoteCounter(dict):
    """Counts votes."""

    def __missing__(self, key):
        return 0


class Votes(TarmacPlugin):
    """Plugin to enforce a voting policy."""

    def run(self, command, target, source, proposal):
        """See L{TarmacPlugin.run}."""
        try:
            criteria = target.config.voting_criteria
        except AttributeError:
            try:
                criteria = command.config.voting_criteria
            except AttributeError:
                return

        votes = self.count_votes(proposal)
        criteria = self.parse_criteria(criteria)

        if not self.evaluate_criteria(votes, criteria):
            votes_desc = ", ".join(
                "%d %s" % (value, vote)
                for (vote, value) in sorted(votes.iteritems()))
            criteria_desc = ", ".join(
                "%s %s %d" % (vote, operator_map_inverse[op], value)
                for (vote, op, value) in criteria)
            lp_comment = (
                u"Voting does not meet specified criteria. "
                u"Required: %s. Got: %s." % (criteria_desc, votes_desc))
            raise VotingViolation(u'Voting criteria not met.', lp_comment)

    def count_votes(self, proposal):
        """Count and collate the votes.

        @return: L{VoteCounter} instance.
        """
        counter = VoteCounter()
        target = proposal.target_branch
        for vote in proposal.votes:
            if not target.isPersonTrustedReviewer(reviewer=vote.reviewer):
                continue
            if vote.is_pending:
                counter[u'Pending'] += 1
            else:
                comment = vote.comment
                if comment is not None and comment.vote != u'Abstain':
                    counter[comment.vote] += 1
        return counter

    def parse_criteria(self, criteria):
        """Parse a given criteria string.

        @param criteria: A string of criteria, separated by commas or
            semi-colons.
        @return: A C{list} of C{(vote, operator, value)} tuples.
        """
        expressions = []
        for expression in criteria_split.split(criteria):
            if len(expression) > 0:
                match = criteria_expr.match(expression)
                if match is None:
                    raise InvalidCriterion('Invalid voting criterion: %s' %
                                           expression)
                else:
                    vote, op, value = match.groups()
                    op, value = operator_map[op], int(value)
                    expressions.append((vote, op, value))
        return expressions

    def evaluate_criteria(self, votes, criteria):
        """Check if the given votes fit the given criteria.

        @param votes: A L{VoteCounter} instance.
        @param criteria: A list of C{(vote, operator, value)} tuples.
        @return: A C{boolean} indicating if the criteria have been met.
        """
        return all(
            op(votes[vote], value)
            for vote, op, value in criteria)


tarmac_hooks['tarmac_pre_commit'].hook(
    Votes(), "Enforces a voting policy.")
