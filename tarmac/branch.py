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

'''Tarmac branch tools.'''
import os
import shutil
import tempfile

from bzrlib import branch as bzr_branch, revision
from bzrlib.workingtree import WorkingTree

from tarmac.config import TarmacConfig
from tarmac.exceptions import BranchHasConflicts


class Branch(object):
    '''Wrapper for working with branches.

    This class wraps the Launchpad branch and the bzrlib branch functionalities
    to work seamlessly with both.
    '''

    def __init__(self, lp_branch, create_tree=False, configuration=None):

        if configuration:
            self.configuration = configuration
        self.has_tree = create_tree
        self.lp_branch = lp_branch
        self.author_list = None
        self.branch = bzr_branch.Branch.open(self.lp_branch.bzr_identity)
        if self.has_tree:
            self._set_up_working_tree()

    def _set_up_working_tree(self):
        '''Create the dir and working tree.'''
        if self.configuration and self.configuration.tree_dir:
            self.tree_dir = self.configuration.tree_dir
        else:
            self.tree_dir = os.path.join(tempfile.gettempdir(),
                self.lp_branch.project.name)
        if os.path.exists(self.tree_dir):
            self.tree = WorkingTree.open(self.tree_dir)
        else:
            self.tree = self.branch.create_checkout(self.tree_dir)
        self.cleanup()
        if not self.author_list:
            self._set_authors()

    def _set_authors(self):
        '''Get the authors from the last revision and use it.'''
        # XXX Need to get all authors from revisions not in target
        last_rev = self.branch.last_revision()
        # Empty the list first since we're going to refresh it
        self.author_list = []
        # Only query for authors if last_rev is not null:
        if last_rev != 'null:':
            rev = self.branch.repository.get_revision(last_rev)
            self.author_list.extend(rev.get_apparent_authors())

    def merge(self, branch):
        '''Merge from another tarmac.branch.Branch instance.'''
        if not self.has_tree:
            raise Exception('This branch wasn\'t set up to do merging,')
        conflict_list = self.tree.merge_from_branch(branch.branch)
        if conflict_list:
            raise BranchHasConflicts

    def cleanup(self):
        '''Remove the working tree from the temp dir.'''
        if self.has_tree:
            self.tree.revert()
            self.tree.update()

    def get_conflicts(self):
        '''Print the conflicts.'''
        assert self.tree.conflicts()
        conflicts = []
        for conflict in self.tree.conflicts():
            conflicts.append(
                u'%s in %s' % (conflict.typestring, conflict.path))
        return '\n'.join(conflicts)

    def commit(self, commit_message, authors=None, **kw):
        '''Commit changes.'''
        if not self.has_tree:
            raise Exception('This branch has no working tree.')
        if not authors:
            authors = self.authors
        elif not self.authors:
            self.author_list = authors
        else:
            self.author_list.append(authors)
        self.tree.commit(commit_message, committer='Tarmac', authors=authors)
        self._set_authors()

    @property
    def landing_candidates(self):
        '''Wrap the LP representation of landing_candidates.'''
        return self.lp_branch.landing_candidates

    @property
    def authors(self):
        if self.author_list is None:
            self._set_authors()
        return self.author_list

    @property
    def has_changes(self):
        if not self.has_tree:
            return False
        return self.tree.changes_from(self.tree.basis_tree())
