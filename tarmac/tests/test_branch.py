# Copyright 2009 Paul Hummer
# Copyright 2009 Canonical Ltd.
#
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

'''Tests for tarmac.branch'''
import os
import unittest

from bzrlib import branch as bzr_branch
from bzrlib.errors import NoCommits
from bzrlib.tests import TestCaseInTempDir

from tarmac import branch
from tarmac.tests.mock import MockLPBranch


#class TestBranch(TestCaseInTempDir):
class DISABLED:
    '''Test for Tarmac.branch.Branch.'''

    #def setUp(self):
    #    '''Set up the test environment.'''
    #    temp_dir = os.path.join(os.getcwd(), "_trial_temp")
    #    os.environ['BZR_HOME'] = temp_dir

    def make_two_branches_to_merge(self):
        '''Make two branches, one with revisions to merge.'''
        a_branch = branch.Branch(MockLPBranch(), create_tree=True)
        a_branch.tree.commit("Reading, 'riting, 'rithmetic")
        another_branch = branch.Branch(MockLPBranch(
            source_branch=a_branch.branch))
        another_branch.lp_branch._internal_tree.commit('ABC...')
        another_branch.lp_branch._internal_tree.commit('...as easy as 123')

        return a_branch, another_branch

    def test_create(self):
        '''Test the creation of a TarmacBranch instance.'''
        a_branch = branch.Branch(MockLPBranch())

        self.assertTrue(isinstance(a_branch, branch.Branch))
        self.assertTrue(isinstance(a_branch.branch, bzr_branch.Branch))
        self.assertTrue(a_branch.lp_branch.bzr_identity)
        self.assertFalse(a_branch.has_tree)
        self.assertFalse(hasattr(a_branch, 'tree'))

    def test_create_with_tree(self):
        '''Test the creation of a TarmacBranch with a created tree.'''
        a_branch = branch.Branch(MockLPBranch(), create_tree=True)

        self.assertTrue(isinstance(a_branch, branch.Branch))
        self.assertTrue(isinstance(a_branch.branch, bzr_branch.Branch))
        self.assertTrue(a_branch.lp_branch.bzr_identity)
        self.assertTrue(a_branch.has_tree)
        self.assertTrue(hasattr(a_branch, 'tree'))

    def test_merge_raises_exception_with_no_tree(self):
        '''A merge on a branch with no tree will raise an exception.'''
        a_branch = branch.Branch(MockLPBranch())
        another_branch = branch.Branch(MockLPBranch())

        self.assertRaises(
            Exception, a_branch.merge, another_branch)

    def test_merge_no_changes(self):
        '''A merge on a branch with a tree will raise an exception if no
        changes are present.'''
        a_branch = branch.Branch(MockLPBranch(), create_tree=True)
        another_branch = branch.Branch(MockLPBranch())

        # XXX: Find a way to generate dummy revisions for the second branch.
        self.assertRaises(NoCommits, a_branch.merge, another_branch)

    def test_merge(self):
        '''A merge on a branch with a tree of a branch with changes will merge.
        '''
        a_branch, another_branch = self.make_two_branches_to_merge()
        a_branch.merge(another_branch)
        a_branch.has_changes

    def test_merge_with_authors(self):
        '''A merge from a branch with authors'''
        branch1 = branch.Branch(MockLPBranch(), create_tree=True)
        branch2 = branch.Branch(MockLPBranch(), create_tree=True)
        authors = [ 'author1', 'author2' ]
        branch1.commit('Authors test', authors=authors)
        branch2.merge(branch1)
        branch2.commit('Authors Merge test', authors=branch1.authors)
        self.assertEquals(branch2.authors.sort(), authors.sort())

    def test_merge_with_reviewers(self):
        '''A merge with reviewers.'''
        reviewers = [ 'reviewer1', 'reviewer2' ]

        a_branch, another_branch = self.make_two_branches_to_merge()
        a_branch.merge(another_branch)
        a_branch.commit('Reviewers test', reviewers=reviewers)

        last_rev = a_branch.lp_branch._internal_bzr_branch.last_revision()
        self.assertNotEquals(last_rev, 'null:')
        rev = a_branch.lp_branch._internal_bzr_branch.repository.get_revision(
            last_rev)
        self.assertEquals('\n'.join(reviewers), rev.properties['reviewers'])

    def test_cleanup(self):
        '''The branch object should clean up after itself.'''
        a_branch, another_branch = self.make_two_branches_to_merge()
        a_branch.merge(another_branch)
        self.assertTrue(a_branch.has_changes)

        a_branch.cleanup()
        self.assertTrue(a_branch.has_changes)
