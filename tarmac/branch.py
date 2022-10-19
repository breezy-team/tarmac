# Copyright 2009 Paul Hummer
# Copyright 2009-2013,2015 Canonical Ltd.
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
from contextlib import ExitStack
import logging
import os
import shutil
import tempfile

from breezy import branch as bzr_branch
from breezy.errors import NoSuchRevision
from breezy.revision import NULL_REVISION
from breezy.workingtree import WorkingTree

from tarmac.config import BranchConfig
from tarmac.exceptions import (
    BranchHasConflicts,
    InvalidWorkingTree,
    TarmacMergeError,
)


class Branch(object):

    def __init__(self, lp_branch, config=False, target=None, launchpad=None):
        self.lp_branch = lp_branch
        self.bzr_branch = bzr_branch.Branch.open(self.lp_branch.bzr_identity)
        if config:
            if lp_branch.bzr_identity in config.branches:
                self.config = BranchConfig(lp_branch.bzr_identity, config)
            else:
                self.config = BranchConfig('lp:' + lp_branch.unique_name,
                                           config)
        else:
            self.config = None

        self.launchpad = launchpad
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
    def create(cls, lp_branch, config, create_tree=False, target=None,
               launchpad=None):
        clazz = cls(lp_branch, config=config, target=target,
                    launchpad=launchpad)
        if create_tree:
            clazz.create_tree()
        return clazz

    def create_tree(self):
        '''Create the dir and working tree.'''
        self.logger.debug(
            'Using tree in %(tree_dir)s' % {
                'tree_dir': self.config.tree_dir})
        if os.path.exists(self.config.tree_dir):
            self.tree = WorkingTree.open(self.config.tree_dir)

            if self.tree.branch.user_url != self.bzr_branch.user_url:
                self.logger.debug('Tree URLs do not match: %s - %s' % (
                    self.bzr_branch.user_url, self.tree.branch.user_url))
                raise InvalidWorkingTree(
                    'The `tree_dir` option for the target branch is not a '
                    'lightweight checkout. Please ask a project '
                    'administrator to resolve the issue, and try again.')
        else:
            self.logger.debug('Tree does not exist.  Creating dir')
            # Create the path up to but not including tree_dir if it does
            # not exist.
            parent_dir = os.path.dirname(self.config.tree_dir)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            self.tree = self.bzr_branch.create_checkout(
                self.config.tree_dir, lightweight=True)

        self.cleanup()

    def cleanup(self):
        '''Remove the working tree from the temp dir.'''
        assert self.tree
        self.tree.revert()
        for filename in [self.tree.abspath(f) for f in self.unmanaged_files]:
            if os.path.isdir(filename) and not os.path.islink(filename):
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
            message = 'Conflicts merging branch.'
            lp_comment = (
                'Attempt to merge into %(target)s failed due to conflicts: '
                '\n\n%(output)s' % {
                    'target': self.lp_branch.display_name,
                    "output": self.conflicts})
            raise BranchHasConflicts(message, lp_comment)

    def merge_tags(self, branch):
        """Merge tags from another branch into this one."""
        branch.tags.merge_to(self.tags, overwrite=True)

    @property
    def unmanaged_files(self):
        """Get the list of ignored and unknown files in the tree."""
        unmanaged = []
        with self.tree.lock_read():
            unmanaged = [x for x in self.tree.unknowns()]
            unmanaged.extend([x[0] for x in self.tree.ignored_files()])
        return unmanaged

    @property
    def conflicts(self):
        '''Print the conflicts.'''
        assert self.tree.conflicts()
        conflicts = []
        for conflict in self.tree.conflicts():
            conflicts.append(
                '%s in %s' % (conflict.typestring, conflict.path))
        return '\n'.join(conflicts)

    def commit(self, commit_message, revprops=None, dry_run=False, **kwargs):
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

        if self.launchpad is not None:
            committer = self.launchpad.me.display_name
        else:
            committer = 'Tarmac'

        if not dry_run:
            self.tree.commit(commit_message, committer=committer,
                             revprops=revprops, authors=authors)

    @property
    def landing_candidates(self):
        '''Wrap the LP representation of landing_candidates.'''
        return self.lp_branch.landing_candidates

    @property
    def authors(self):
        author_list = []

        if self.target:
            with ExitStack() as es:
                es.enter_context(self.bzr_branch.lock_read())
                es.enter_context(self.target.bzr_branch.lock_read())

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

        else:
            last_rev = self.bzr_branch.last_revision()
            if last_rev != NULL_REVISION:
                rev = self.bzr_branch.repository.get_revision(last_rev)
                apparent_authors = rev.get_apparent_authors()
                author_list.extend(
                    [a.replace('\n', '') for a in apparent_authors])

        return author_list

    @property
    def fixed_bugs(self):
        """Return the list of bugs fixed by the branch."""
        bugs_list = []

        with self.bzr_branch.lock_read():
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

        return bugs_list

    @property
    def tags(self):
        """Return the Tags container for the bzr_branch."""
        return self.bzr_branch.tags
