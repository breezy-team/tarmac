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
import shutil
import tempfile

from bzrlib import branch as bzr_branch
from bzrlib.errors import NoSuchRevision
from bzrlib.workingtree import WorkingTree

from tarmac.config import BranchConfig
from tarmac.exceptions import BranchHasConflicts, TarmacMergeError


class Branch(object):

    def __init__(self, lp_branch, config=False, target=None):
        self.lp_branch = lp_branch
        self.bzr_branch = bzr_branch.Branch.open(self.lp_branch.bzr_identity)
        if config:
            self.config = BranchConfig(lp_branch.bzr_identity, config)
        else:
            self.config = None

        self.target = target
        self.logger = logging.getLogger('tarmac')

    def __del__(self):
        """Do some potenetially necessary cleanup during deletion."""
        try:
            # If we were using a temp directory, then remove it
            shutil.rmtree(self.temp_tree_dir)
        except AttributeError:
            # Not using a tempdir
            pass

    @classmethod
    def create(cls, lp_branch, config, create_tree=False, target=None):
        clazz = cls(lp_branch, config, target)
        if create_tree:
            clazz.create_tree()
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
            # Store this so we can rmtree later
            self.temp_tree_dir = tempfile.mkdtemp()
            self.logger.debug(
                'Using temp dir at %(tree_dir)s' % {
                    'tree_dir': self.temp_tree_dir})
            self.tree = self.bzr_branch.create_checkout(self.temp_tree_dir)

        self.cleanup()

    def cleanup(self):
        '''Remove the working tree from the temp dir.'''
        assert self.tree
        self.tree.revert()
        for filename in [self.tree.abspath(f) for f in self.unmanaged_files]:
            if os.path.isdir(filename):
                shutil.rmtree(filename)
            else:
                os.remove(filename)

        self.tree.update()

    def merge(self, branch, revid=None):
        '''Merge from another tarmac.branch.Branch instance.'''
        assert self.tree
        conflict_list = self.tree.merge_from_branch(
            branch.bzr_branch, to_revision=revid)
        if conflict_list:
            message = u'Conflicts merging branch.'
            lp_comment = (
                u'Attempt to merge into %(target)s failed due to conflicts: '
                u'\n\n%(output)s' % {
                    'target': self.lp_branch.display_name,
                    "output": self.conflicts})
            raise BranchHasConflicts(message, lp_comment)

    @property
    def unmanaged_files(self):
        """Get the list of ignored and unknown files in the tree."""
        self.tree.lock_read()
        unmanaged = [x for x in self.tree.unknowns()]
        unmanaged.extend([x[0] for x in self.tree.ignored_files()])
        self.tree.unlock()
        return unmanaged

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
        if not revprops:
            revprops = {}

        authors = kwargs.pop('authors', None)
        reviews = kwargs.pop('reviews', None)

        if not authors:
            authors = self.authors

        if reviews:
            for review in reviews:
                if '\n' in review:
                    raise TarmacMergeError('\\n is not a valid character in a '
                                           'review identity or vote.')
            revprops['reviews'] = '\n'.join(reviews)

        self.tree.commit(commit_message, committer='Tarmac',
                         revprops=revprops, authors=authors)

    @property
    def landing_candidates(self):
        '''Wrap the LP representation of landing_candidates.'''
        return self.lp_branch.landing_candidates

    @property
    def authors(self):
        author_list = []

        if self.target:
            self.bzr_branch.lock_read()
            self.target.bzr_branch.lock_read()

            graph = self.bzr_branch.repository.get_graph(
                self.target.bzr_branch.repository)

            unique_ids = graph.find_unique_ancestors(
                self.bzr_branch.last_revision(),
                [self.target.bzr_branch.last_revision()])

            revs = self.bzr_branch.repository.get_revisions(unique_ids)
            for rev in revs:
                apparent_authors = rev.get_apparent_authors()
                for author in apparent_authors:
                    author.replace('\n', '')
                    if author not in author_list:
                        author_list.append(author)

            self.target.bzr_branch.unlock()
            self.bzr_branch.unlock()
        else:
            last_rev = self.bzr_branch.last_revision()
            if last_rev != 'null:':
                rev = self.bzr_branch.repository.get_revision(last_rev)
                apparent_authors = rev.get_apparent_authors()
                author_list.extend(
                    [a.replace('\n', '') for a in apparent_authors])

        return author_list

    @property
    def fixed_bugs(self):
        """Return the list of bugs fixed by the branch."""
        bugs_list = []

        self.bzr_branch.lock_read()
        oldrevid = self.bzr_branch.get_rev_id(self.lp_branch.revision_count)
        for rev_info in self.bzr_branch.iter_merge_sorted_revisions(
            stop_revision_id=oldrevid):
            try:
                rev = self.bzr_branch.repository.get_revision(rev_info[0])
                for bug in rev.iter_bugs():
                    if bug[0].startswith('https://launchpad.net/bugs/'):
                        bugs_list.append(bug[0].replace(
                                'https://launchpad.net/bugs/', ''))
            except NoSuchRevision:
                continue

        self.bzr_branch.unlock()
        return bugs_list
