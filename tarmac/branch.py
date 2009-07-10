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

from bzrlib import branch as bzr_branch, revision


class Branch(object):
    '''Wrapper for working with branches.

    This class wraps the Launchpad branch and the bzrlib branch functionalities
    to work seamlessly with both.
    '''

    def __init__(self, lp_branch, create_tree=False):

        self.has_tree = create_tree
        self.lp_branch = lp_branch
        self.author_list = None
        self.branch = bzr_branch.Branch.open(self.lp_branch.bzr_identity)
        if self.has_tree:
            self._set_up_working_tree()

    def _set_up_working_tree(self):
        '''Create the dir and working tree.'''
        self.temporary_dir = os.path.join('/tmp', self.lp_branch.project.name)
        if os.path.exists(self.temporary_dir):
            shutil.rmtree(self.temporary_dir)
        self.tree = self.branch.create_checkout(self.temporary_dir)
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
        self.tree.merge_from_branch(branch.branch)

    def cleanup(self):
        '''Remove the working tree from the temp dir.'''
        if self.has_tree:
            self._set_up_working_tree()

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
