# Copyright 2009 Paul Hummer
# Copyright 2009 Canonical Ltd.
#
# This file is part of Tarmac.
#
# Authors: Paul Hummer
#          Rodney Dawes
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

from tarmac.config import BranchConfig
from tarmac.exceptions import BranchHasConflicts


class Branch(object):

    def __init__(self, lp_branch, config):
        assert config.has_section(lp_branch.bzr_identity)

        self.lp_branch = lp_branch
        self.config = BranchConfig(lp_branch.bzr_identity, config)

    @classmethod
    def create(cls, lp_branch, config, create_tree=False):
        clazz = cls(lp_branch, config)
        if create_tree:
            clazz.create_tree()
        return clazz

    def create_tree(self):
        '''Create the dir and working tree.'''
        if self.config.tree_dir:
            if os.path.exists(self.config.tree_dir):
                self.tree = WorkingTree.open(self.config.tree_dir)
            else:
                _branch = bzr_branch.Branch.open(self.lp_branch.bzr_identity)
                self.tree = _branch.create_checkout(self.tree_dir)
        else:
            self.tree_dir = tempfile.mkdtemp()
            _branch = bzr_branch.Branch.open(self.lp_branch.bzr_identity)
            self.tree = _branch.create_checkout(self.tree_dir)

        self.cleanup()

    def cleanup(self):
        '''Remove the working tree from the temp dir.'''
        if self.tree_dir:
            self.tree.revert()
            self.tree.update()

    def merge(self, branch):
        '''Merge from another tarmac.branch.Branch instance.'''
        if not self.tree_dir:
            raise Exception('This branch wasn\'t set up to do merging,')
        branch = bzr_branch.Branch.open(branch.lp_branch.bzr_identity)
        conflict_list = self.tree.merge_from_branch(branch)
        if conflict_list:
            raise BranchHasConflicts



    # TODO: Deal with the fallout of removing the old Branch implementation
    def _set_authors(self):
        '''Get the authors from the last revision and use it.'''
        # XXX: Need to get all authors from revisions not in target.
        last_rev = self.branch.last_revision()
        # Empty the list first since we're going to refresh it
        self.author_list = []
        # Only query for authors if last_rev is not null:
        if last_rev != 'null:':
            rev = self.branch.repository.get_revision(last_rev)
            apparent_authors = rev.get_apparent_authors()
            self.author_list.extend(
                [a.replace('\n', '') for a in apparent_authors])

    def get_conflicts(self):
        '''Print the conflicts.'''
        assert self.tree.conflicts()
        conflicts = []
        for conflict in self.tree.conflicts():
            conflicts.append(
                u'%s in %s' % (conflict.typestring, conflict.path))
        return '\n'.join(conflicts)

    def commit(self, commit_message, revprops=None, **kwargs):
        '''Commit changes.'''
        if not self.has_tree:
            raise Exception('This branch has no working tree.')

        if not revprops:
            revprops = {}

        authors = kwargs.pop('authors', None)
        reviewers = kwargs.pop('reviewers', None)

        if not authors:
            authors = self.authors
        elif not self.authors:
            self.author_list = authors
        else:
            self.author_list.append(authors)

        if reviewers:
            for reviewer in reviewers:
                if '\n' in reviewer:
                    raise AssertionError('\\n is not a valid character in a '
                                         ' reviewer identity')
            revprops['reviewers'] = '\n'.join(reviewers)

        self.tree.commit(commit_message, committer='Tarmac',
                         revprops=revprops, authors=authors)
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
