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



tarmac_hooks['tarmac_pre_commit'].hook(
    Votes(), "Enforces a voting policy.")
