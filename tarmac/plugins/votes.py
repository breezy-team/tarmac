# Copyright 2009 Paul Hummer
# This file is part of Tarmac.
#
# Tarmac is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by
# the Free Software Foundation.
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


class VotingViolation(Exception):
    """The voting criteria have not been met."""


class VoteCounter(dict):
    """Counts votes."""

    def __missing__(self, key):
        return 0


class Votes(TarmacPlugin):
    """Plugin to enforce a voting policy."""

    def run(self, command, target, source, proposal):
        try:
            criteria = target.config.voting_criteria
        except AttributeError:
            return

        votes = self.count_votes(proposal.votes)
        criteria = self.parse_criteria(criteria)

        if not self.evaluate_criteria(votes, criteria):
            votes_desc = ", ".join(
                "%d %s" % (value, vote)
                for (vote, value) in sorted(votes.iteritems()))
            criteria_desc = ", ".join(
                "%s %s %d" % (vote, operator_map_inverse[op], value)
                for (vote, op, value) in criteria)
            raise VotingViolation(
                "Voting does not meet specified criteria. "
                 "Required: %s. Got: %s." % (criteria_desc, votes_desc))

    def count_votes(self, votes):
        counter = VoteCounter()
        for vote in votes:
            comment = vote.comment
            if comment is not None:
                counter[comment.vote] += 1
        return counter

    def parse_criteria(self, criteria):
        expressions = []
        for expression in criteria_split.split(criteria):
            if len(expression) > 0:
                match = criteria_expr.match(expression)
                if match is None:
                    raise InvalidCriterion(expression)
                else:
                    vote, op, value = match.groups()
                    op, value = operator_map[op], int(value)
                    expressions.append((vote, op, value))
        return expressions

    def evaluate_criteria(self, votes, criteria):
        for vote, op, value in criteria:
            if not op(votes[vote], value):
                return False
        return True


tarmac_hooks['tarmac_pre_commit'].hook(
    Votes(), "Enforces a voting policy.")
