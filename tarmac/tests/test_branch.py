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

from bzrlib.errors import PointlessMerge

from tarmac import branch
from tarmac.tests import TarmacTestCase
from tarmac.tests.mock import MockLPBranch


class TestBranch(TarmacTestCase):
    '''Test for Tarmac.branch.Branch.'''

    def setUp(self):
        '''Set up the test environment.'''
        TarmacTestCase.setUp(self)

        self.bzrdir = os.path.join(os.getcwd(), "bzr")
        os.environ['BZR_HOME'] = self.bzrdir

        self.branch1, self.branch2 = self.make_two_branches_to_merge()

    def tearDown(self):
        """Tear down the tests."""
        self.remove_branch_config(self.branch1.lp_branch.tree_dir)
        self.remove_branch_config(self.branch2.lp_branch.tree_dir)
        TarmacTestCase.tearDown(self)

    def make_two_branches_to_merge(self):
        '''Make two branches, one with revisions to merge.'''
        branch1_dir = os.path.join(self.tempdir, 'branch1')
        branch2_dir = os.path.join(self.tempdir, 'branch2')
        self.add_branch_config(branch1_dir)
        self.add_branch_config(branch2_dir)

        mock1 = MockLPBranch(branch1_dir)
        branch1 = branch.Branch.create(mock1, self.config, create_tree=True)
        branch1.commit("Reading, 'riting, 'rithmetic")
        branch1.lp_branch.revision_count += 1

        mock2 = MockLPBranch(branch2_dir, source_branch=branch1.lp_branch)
        branch2 = branch.Branch.create(mock2, self.config, create_tree=True)
        branch2.commit('ABC...')

        added_file = os.path.join(branch2.lp_branch.tree_dir, 'README')
        with open(added_file, 'w+') as f:
            f.write('This is a test file.')
            f.close()
        branch2.tree.add(['README'])
        branch2.commit('Added a README for testing')
        branch2.lp_branch.revision_count += 2

        return branch1, branch2

    def test_create(self):
        '''Test the creation of a TarmacBranch instance.'''
        tree_dir = os.path.join(self.tempdir, 'test_create')
        self.add_branch_config(tree_dir)

        a_branch = branch.Branch.create(MockLPBranch(tree_dir), self.config)
        self.assertTrue(isinstance(a_branch, branch.Branch))
        self.assertTrue(a_branch.lp_branch.bzr_identity is not None)
        self.assertFalse(hasattr(a_branch, 'tree'))
        self.remove_branch_config(tree_dir)

    def test_create_with_tree(self):
        '''Test the creation of a TarmacBranch with a created tree.'''
        self.assertTrue(isinstance(self.branch1, branch.Branch))
        self.assertTrue(self.branch1.lp_branch.bzr_identity is not None)
        self.assertTrue(hasattr(self.branch1, 'tree'))

    def test_merge_raises_exception_with_no_tree(self):
        '''A merge on a branch with no tree will raise an exception.'''
        branch3_dir = os.path.join(self.tempdir, 'branch3')
        self.add_branch_config(branch3_dir)
        branch3 = branch.Branch.create(MockLPBranch(
                branch3_dir, source_branch=self.branch1.lp_branch),
                                       self.config)

        self.assertRaises(
            AttributeError, branch3.merge, self.branch2)
        self.remove_branch_config(branch3_dir)

    def test_merge_no_changes(self):
        '''A merge on a branch with a tree will raise an exception if no
        changes are present.'''
        branch3_dir = os.path.join(self.tempdir, 'branch3')
        self.add_branch_config(branch3_dir)
        branch3 = branch.Branch.create(MockLPBranch(
                branch3_dir, source_branch=self.branch1.lp_branch),
                                       self.config)

        self.assertRaises(PointlessMerge, self.branch1.merge, branch3)
        self.remove_branch_config(branch3_dir)

    def test_merge(self):
        '''A merge on a branch with a tree of a branch with changes will merge.
        '''
        self.branch1.merge(self.branch2)
        self.assertTrue(self.branch1.tree.changes_from(
                self.branch1.tree.basis_tree()).has_changed())

    def test_merge_with_authors(self):
        '''A merge from a branch with authors'''
        authors = [ 'author1', 'author2' ]
        self.branch1.commit('Authors test', authors=authors)
        self.branch2.merge(self.branch1)
        self.branch2.commit('Authors Merge test', authors=self.branch1.authors)
        self.assertEqual(self.branch2.authors.sort(), authors.sort())

    def test_merge_with_bugs(self):
        '''A merge from a branch with authors'''
        bugs = ['https://launchpad.net/bugs/1 fixed',
                'https://bugzilla.gnome.org/show_bug.cgi?id=1 fixed',
                'https://launchpad.net/bugs/2 fixed'
                ]
        revprops = {}
        revprops['bugs'] = '\n'.join(bugs)
        self.branch1.commit('Bugs test', revprops)
        self.branch1.commit('Testing')
        self.branch2.commit('Foo',
                            revprops={
                'bugs':'https://launchpad.net/bugs/3 fixed'})
        self.branch2.lp_branch.revision_count += 1
        self.branch2.merge(self.branch1)
        self.branch2.commit('Landed bugs')
        self.assertEqual(self.branch2.fixed_bugs, self.branch1.fixed_bugs)

    def test_merge_with_reviewers(self):
        '''A merge with reviewers.'''
        reviewers = [ 'reviewer1', 'reviewer2' ]
        self.branch1.merge(self.branch2)
        self.branch1.commit('Reviewers test', reviewers=reviewers)

        last_rev = self.branch1.lp_branch._internal_bzr_branch.last_revision()
        self.assertNotEquals(last_rev, 'null:')
        repo = self.branch1.lp_branch._internal_bzr_branch.repository
        rev = repo.get_revision(last_rev)
        self.assertEquals('\n'.join(reviewers), rev.properties['reviewers'])

    def test_cleanup(self):
        '''The branch object should clean up after itself.'''
        self.branch1.merge(self.branch2)
        self.assertTrue(self.branch1.tree.changes_from(
                self.branch1.tree.basis_tree()).has_changed())
        self.branch1.cleanup()
        self.assertFalse(self.branch1.tree.changes_from(
                self.branch1.tree.basis_tree()).has_changed())
