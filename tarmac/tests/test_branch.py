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

'''Tests for tarmac.branch'''
import os
import unittest

from bzrlib import branch as bzr_branch
from bzrlib.errors import NoCommits

from tarmac import branch
from tarmac.tests.mock import MockLPBranch


class TestBranch(unittest.TestCase):
    '''Test for Tarmac.branch.Branch.'''

    def setUp(self):
        '''Set up the test environment.'''
        temp_dir = os.path.join(os.getcwd(), "_trial_temp")
        os.environ['BZR_HOME'] = temp_dir

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

    def test_merge(self):
        '''A merge on a branch with a tree will succeed.'''
        a_branch = branch.Branch(MockLPBranch(), create_tree=True)
        another_branch = branch.Branch(MockLPBranch())

        # XXX: Find a way to generate dummy revisions for the second branch.
        self.assertRaises(NoCommits, a_branch.merge, another_branch)

    def test_merge_with_authors(self):
        '''A merge from a branch with authors'''
        branch1 = branch.Branch(MockLPBranch(), create_tree=True)
        branch2 = branch.Branch(MockLPBranch(), create_tree=True)
        authors = [ 'author1', 'author2' ]
        branch1.commit('Authors test', authors=authors)
        branch2.merge(branch1)
        branch2.commit('Authors Merge test', authors=branch1.authors)
        self.assertEquals(branch2.authors.sort(), authors.sort())

    def DISABLEDtest_cleanup(self):
        '''The branch object should clean up after itself.'''
        a_branch = branch.Branch(MockLPBranch(), create_tree=True)
        self.assertTrue(os.path.exists(a_branch.temporary_dir))

        a_branch.cleanup()
        self.assertFalse(os.path.exists(a_branch.temporary_dir))

