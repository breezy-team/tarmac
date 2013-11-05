# Copyright 2009 Paul Hummer
# Copyright 2013 Canonical Ltd.
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

'''Tarmac specific exceptions.'''

from bzrlib.errors import BzrCommandError


class TarmacMergeError(Exception):
    """An error occurred, preventing the merge of a branch."""

    def __init__(self, message, comment=None, *args, **kwargs):
        super(TarmacMergeError, self).__init__(message, *args, **kwargs)
        self.comment = comment


class BranchHasConflicts(TarmacMergeError):
    '''Exception for when a branch merge has conflicts.'''


class CommandNotFound(Exception):
    '''Exception for calling a command that that hasn't been registered.'''


class InvalidWorkingTree(TarmacMergeError):
    """Exception for invalid working tree (not a lightweight checkout)."""


class TarmacCommandError(BzrCommandError):
    '''Exception for various command errors.'''


class UnapprovedChanges(TarmacMergeError):
    '''Exception for when a branch has unapproved changes.'''


class TarmacMergeSkipError(Exception):
    """Exception to raise for non-fatal errors that should skip the merge."""
