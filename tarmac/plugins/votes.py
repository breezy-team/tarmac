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

"""Tarmac plugin for enforcing a minimum number of approval votes."""

import operator
import re

from tarmac.hooks import tarmac_hooks
from tarmac.plugins import TarmacPlugin


class VoteCounter(dict):
    """Counts votes."""

    def __missing__(self, key):
        return 0


class Votes(TarmacPlugin):
    """Plugin to enforce a voting policy."""

    def __call__(self, command, target, source, proposal):
        pass

    def count_votes(self, proposal):
        counter = VoteCounter()
        for vote in proposal.votes:
            comment = vote.comment
            if comment is not None:
                counter[comment.vote] += 1
        return counter

    def parse_criteria(self, criteria):
        operator_map = {
            "=": operator.eq,
            "==": operator.eq,
            "<": operator.lt,
            "<=": operator.le,
            ">=": operator.ge,
            ">": operator.gt,
            }
        operator_expr = "|".join(re.escape(op) for op in operator_map)
        vote_expr = "[a-zA-Z ]+"
        number_expr = "[0-9]+"
        term_expr = r"(%s) \s* (%s) \s* (%s)" % (
            vote_expr, operator_expr, number_expr)
        term_expr_flags = re.VERBOSE | re.MULTILINE
        exprs = re.findall(term_expr, criteria, term_expr_flags)
        for (vote, op, value) in exprs:
            yield vote.strip(), operator_map[op], int(value)

    def evaluate_criteria(self, votes, criteria):
        for vote, op, value in criteria:
            if not op(votes[vote], value):
                return False
        return True


tarmac_hooks['tarmac_pre_commit'].hook(
    Votes(), "Enforces a voting policy.")
