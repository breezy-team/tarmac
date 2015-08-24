# Copyright 2009 Paul Hummer
# Copyright 2009-2013 Canonical Ltd.
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
import shutil

from bzrlib.errors import PointlessMerge
from mock import patch
from tarmac import branch
from tarmac.exceptions import (
    InvalidWorkingTree,
    TarmacMergeError,
)
from tarmac.tests import (
    BranchTestCase,
    MockLPBranch,
    Thing,
)


class TestBranch(BranchTestCase):
    '''Test for Tarmac.branch.Branch.'''

    def test_use_unique_name_fallback(self):
        """Test that unique_name is used if bzr_identity isn't."""
        tree_dir = os.path.join(self.TEST_ROOT, 'test_unique_name')
        mock = MockLPBranch(tree_dir)
        mock.unique_name = 'lp:~owner/project/name'
        self.config.add_section(mock.unique_name)
        self.config.set(mock.unique_name, 'tree_dir', tree_dir)
        a_branch = branch.Branch.create(mock, self.config)
        self.assertEqual(tree_dir, a_branch.config.tree_dir)
        self.config.remove_section(mock.unique_name)

    def test_create(self):
        '''Test the creation of a TarmacBranch instance.'''
        tree_dir = os.path.join(self.TEST_ROOT, 'test_create')
        self.add_branch_config(tree_dir)

        a_branch = branch.Branch.create(MockLPBranch(tree_dir), self.config)
        self.assertTrue(isinstance(a_branch, branch.Branch))
        self.assertTrue(a_branch.lp_branch.bzr_identity is not None)
        self.assertFalse(hasattr(a_branch, 'tree'))
        self.remove_branch_config(tree_dir)

    def test_create_missing_parent_dir(self):
        '''Test the creation of a TarmacBranch instance in a path that does
        not fully exist, with a tree'''
        branch_name = 'test_branch'
        parent_dir = os.path.join(self.TEST_ROOT, 'missing')
        tree_dir = os.path.join(parent_dir, branch_name)
        self.add_branch_config(tree_dir)
        # Create the mock somewhere other than where the tarmac branch will be
        # located.  Keep it right under TEST_ROOT so the
        # TarmacDirectoryFactory mocking will work.
        mock = MockLPBranch(os.path.join(self.TEST_ROOT, branch_name))
        self.assertFalse(os.path.exists(parent_dir))
        a_branch = branch.Branch.create(mock, self.config, create_tree=True)
        self.assertTrue(os.path.exists(parent_dir))
        self.assertTrue(isinstance(a_branch, branch.Branch))
        self.assertTrue(a_branch.lp_branch.bzr_identity is not None)
        self.assertTrue(hasattr(a_branch, 'tree'))
        self.remove_branch_config(tree_dir)

    def test_create_with_tree(self):
        '''Test the creation of a TarmacBranch with a created tree.'''
        self.assertTrue(isinstance(self.branch1, branch.Branch))
        self.assertTrue(self.branch1.lp_branch.bzr_identity is not None)
        self.assertTrue(hasattr(self.branch1, 'tree'))

    def test_merge_raises_exception_with_no_tree(self):
        '''A merge on a branch with no tree will raise an exception.'''
        branch3_dir = os.path.join(self.TEST_ROOT, 'branch3')
        self.add_branch_config(branch3_dir)
        branch3 = branch.Branch.create(MockLPBranch(
                branch3_dir, source_branch=self.branch1.lp_branch),
                                       self.config)

        self.assertRaises(
            AttributeError, branch3.merge, self.branch2)
        self.remove_branch_config(branch3_dir)
        shutil.rmtree(branch3_dir)

    def test_merge_no_changes(self):
        '''A merge on a branch with a tree will raise an exception if no
        changes are present.'''
        branch3_dir = os.path.join(self.TEST_ROOT, 'branch3')
        self.add_branch_config(branch3_dir)
        branch3 = branch.Branch.create(MockLPBranch(
                branch3_dir, source_branch=self.branch1.lp_branch),
                                       self.config)

        self.assertRaises(PointlessMerge, self.branch1.merge, branch3)
        self.remove_branch_config(branch3_dir)
        shutil.rmtree(branch3_dir)

    def test_merge(self):
        '''A merge on a branch with a tree of a branch with changes will merge.
        '''
        self.branch1.merge(self.branch2)
        self.assertTrue(self.branch1.tree.changes_from(
                self.branch1.tree.basis_tree()).has_changed())

    def test_merge_tags(self):
        """Test that merging tags works as expected."""
        tag_name = 'tag1'
        self.branch2.commit('Just a tag.')
        self.branch2.lp_branch.revision_count += 1
        tag_revision_id = self.branch2.bzr_branch.get_rev_id(
            self.branch2.lp_branch.revision_count)
        self.branch2.tags.set_tag(tag_name, tag_revision_id)
        self.branch1.merge(self.branch2)
        self.branch1.merge_tags(self.branch2)
        self.assertEqual(self.branch1.tags.lookup_tag(tag_name),
                         tag_revision_id)

    def test_merge_tags_overwrite(self):
        """Test that merging tags overwrites tags as expected."""
        tag_name = 'tag1'
        self.branch1.commit('First commit, with a tag.')
        self.branch1.lp_branch.revision_count += 1
        tag_revision_id1 = self.branch1.bzr_branch.get_rev_id(
            self.branch1.lp_branch.revision_count)
        self.branch1.tags.set_tag(tag_name, tag_revision_id1)
        self.branch2.merge(self.branch1)
        self.branch2.commit('Merged branch1')
        self.branch2.commit('Just a tag.')
        self.branch2.lp_branch.revision_count += 2
        tag_revision_id2 = self.branch2.bzr_branch.get_rev_id(
            self.branch2.lp_branch.revision_count)
        self.branch2.tags.set_tag(tag_name, tag_revision_id2)
        self.branch1.merge(self.branch2)
        self.branch1.merge_tags(self.branch2)
        self.assertEqual(self.branch1.tags.lookup_tag(tag_name),
                         tag_revision_id2)

    def test_merge_with_authors(self):
        '''A merge from a branch with authors'''
        authors = ['author1', 'author2']
        self.branch2.commit('Authors test', authors=authors)
        self.branch2.commit('Another author', authors=['author3'])
        self.branch2.lp_branch.revision_count += 2
        orig_authors = self.branch2.authors
        self.branch1.merge(self.branch2)
        self.branch1.commit('Authors Merge test', authors=self.branch2.authors)
        self.branch1.lp_branch.revision_count += 1
        self.assertEqual(sorted(orig_authors),
                         sorted(self.branch1.authors))

    def test_merge_with_bugs(self):
        '''A merge from a branch with authors'''
        bugs = ['https://launchpad.net/bugs/1 fixed',
                'https://bugzilla.gnome.org/show_bug.cgi?id=1 fixed',
                'https://launchpad.net/bugs/2 fixed']
        revprops = {}
        revprops['bugs'] = '\n'.join(bugs)
        self.branch1.commit('Bugs test', revprops)
        self.branch1.commit('Testing')
        self.branch2.commit(
            'Foo', revprops={'bugs': 'https://launchpad.net/bugs/3 fixed'})
        self.branch2.lp_branch.revision_count += 1
        self.branch2.merge(self.branch1)
        self.branch2.commit('Landed bugs')
        self.assertEqual(self.branch2.fixed_bugs, self.branch1.fixed_bugs)

    def test_merge_with_reviews(self):
        '''A merge with reviewers.'''
        reviews = ['reviewer1 Approve', 'reviewer2 Abstain']
        self.branch1.merge(self.branch2)
        self.branch1.commit('Reviewers test', reviews=reviews)

        last_rev = self.branch1.lp_branch._internal_bzr_branch.last_revision()
        self.assertNotEquals(last_rev, 'null:')
        repo = self.branch1.lp_branch._internal_bzr_branch.repository
        rev = repo.get_revision(last_rev)
        self.assertEquals('\n'.join(reviews),
                          rev.properties.get('reviews', None))

    def test_cleanup(self):
        '''The branch object should clean up after itself.'''
        self.branch1.merge(self.branch2)
        self.assertTrue(self.branch1.tree.changes_from(
                self.branch1.tree.basis_tree()).has_changed())
        with open(os.path.join(self.branch1.config.tree_dir, 'README.bak~'),
                  'w') as f:
            f.close()

        self.branch1.cleanup()
        self.assertFalse(self.branch1.tree.changes_from(
                self.branch1.tree.basis_tree()).has_changed())

    def test_unmanaged_files(self):
        """Test that the unmanaged_files property returns correct lists."""
        self.branch1.merge(self.branch2)
        self.assertEqual(self.branch1.unmanaged_files, [])
        expected = sorted([u'README~', u'newfile'])
        with open(os.path.join(self.branch1.config.tree_dir, 'README~'),
                  'w') as f:
            f.close()
        with open(os.path.join(self.branch1.config.tree_dir, 'newfile'),
                  'w') as f:
            f.close()
        self.assertEqual(sorted(self.branch1.unmanaged_files), expected)
        self.branch1.cleanup()
        self.assertEqual(self.branch1.unmanaged_files, [])

    def test_commit_with_author_with_newline(self):
        """Test that committing a branch with an author containing \n fails."""
        authors = ['author1', 'author2']
        self.assertRaises(TarmacMergeError,
                          self.branch2.commit,
                          'Authors Merge test', authors=['\n'.join(authors)])

    @patch('tarmac.branch.bzr_branch.Branch.user_url')
    def test_create_tree_invalid_workingtree(self, mocked):
        """Test that InvalidWorkingTree is raised when it should be."""
        tree_dir = os.path.join(self.TEST_ROOT, 'test_invalid_workingtree')
        self.add_branch_config(tree_dir)
        self.addCleanup(self.remove_branch_config, tree_dir)
        a_branch = branch.Branch(MockLPBranch(tree_dir), self.config)
        a_branch.bzr_branch.user_url = 'lp:invalid'
        self.assertRaises(InvalidWorkingTree,
                          a_branch.create_tree)

    def test_committer_is_launchpad_user(self):
        """Test that the committer when committing, is the LP user's name."""
        tree_dir = os.path.join(self.TEST_ROOT, 'test_lp_committer')
        self.add_branch_config(tree_dir)
        self.addCleanup(self.remove_branch_config, tree_dir)
        self.addCleanup(shutil.rmtree, tree_dir)

        committer = 'LP User'
        a_branch = branch.Branch.create(MockLPBranch(tree_dir), self.config,
                                        create_tree=True, launchpad=Thing(
                                            me=Thing(display_name=committer)))
        a_branch.commit('Test LP User.')
        self.assertEqual(committer, a_branch.authors[0])
