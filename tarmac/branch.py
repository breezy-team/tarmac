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
import logging
import os
import tempfile

from bzrlib import branch as bzr_branch
from bzrlib.workingtree import WorkingTree

from tarmac.config import BranchConfig
from tarmac.exceptions import BranchHasConflicts


class Branch(object):

    def __init__(self, lp_branch, config=False):
        self.lp_branch = lp_branch
        self.bzr_branch = bzr_branch.Branch.open(self.lp_branch.bzr_identity)
        if config:
            self.config = BranchConfig(lp_branch.bzr_identity, config)
        else:
            self.config = None

        self.logger = logging.getLogger('tarmac')

    @classmethod
    def create(cls, lp_branch, config, create_tree=False):
        if create_tree:
            assert config.has_section(lp_branch.bzr_identity)
            clazz = cls(lp_branch, config)
            clazz.create_tree()
        else:
            clazz = cls(lp_branch)
        return clazz

    def create_tree(self):
        '''Create the dir and working tree.'''
        try:
            self.logger.debug(
                'Using tree in %(tree_dir)s' % {
                    'tree_dir': self.config.tree_dir})
            if os.path.exists(self.config.tree_dir):
                self.tree = WorkingTree.open(self.config.tree_dir)
            else:
                self.logger.debug('Tree does not exist.  Creating dir')
                self.tree = self.bzr_branch.create_checkout(
                    self.config.tree_dir, lightweight=True)
        except AttributeError:
            tree_dir = tempfile.mkdtemp()
            self.logger.debug(
                'Using temp dir at %(tree_dir)s' % {
                    'tree_dir': tree_dir})
            self.tree = self.bzr_branch.create_checkout(tree_dir)

        self.cleanup()

    def cleanup(self):
        '''Remove the working tree from the temp dir.'''
        assert self.tree
        self.tree.revert()
        for unknown in self.tree.unknowns():
            os.remove(unknown)

        self.tree.update()

    def merge(self, branch, revid=None):
        '''Merge from another tarmac.branch.Branch instance.'''
        assert self.tree
        conflict_list = self.tree.merge_from_branch(
            branch.bzr_branch, to_revision=revid)
        if conflict_list:
            raise BranchHasConflicts

    @property
    def conflicts(self):
        '''Print the conflicts.'''
        assert self.tree.conflicts()
        conflicts = []
        for conflict in self.tree.conflicts():
            conflicts.append(
                u'%s in %s' % (conflict.typestring, conflict.path))
        return '\n'.join(conflicts)

    def commit(self, commit_message, revprops=None, **kwargs):
        '''Commit changes.'''
        assert self.tree

        if not revprops:
            revprops = {}

        authors = kwargs.pop('authors', None)
        reviewers = kwargs.pop('reviewers', None)

        if not authors:
            authors = self.authors

        if reviewers:
            for reviewer in reviewers:
                if '\n' in reviewer:
                    raise AssertionError('\\n is not a valid character in a '
                                         ' reviewer identity')
            revprops['reviewers'] = '\n'.join(reviewers)

        self.tree.commit(commit_message, committer='Tarmac',
                         revprops=revprops, authors=authors)

    @property
    def landing_candidates(self):
        '''Wrap the LP representation of landing_candidates.'''
        return self.lp_branch.landing_candidates

    @property
    def authors(self):
        last_rev = self.bzr_branch.last_revision()
        author_list = []

        # Only query for authors if last_rev is not null:
        if last_rev != 'null:':
            rev = self.bzr_branch.repository.get_revision(last_rev)
            apparent_authors = rev.get_apparent_authors()
            author_list.extend(
                [a.replace('\n', '') for a in apparent_authors])
        return author_list

    @property
    def has_changes(self):
        if not self.has_tree:
            return False
        return self.tree.changes_from(self.tree.basis_tree())
