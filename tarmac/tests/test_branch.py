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

from bzrlib.errors import NoCommits

from tarmac import branch
from tarmac.config import TarmacConfig
from tarmac.tests import TarmacTestCase
from tarmac.tests.mock import MockLPBranch

CONFIG_TEMPLATE = '''
[%(url)s]
tree_dir = %(temp_tree)s
log_file = %(temp_log)s
'''


class TestBranch(TarmacTestCase):
    '''Test for Tarmac.branch.Branch.'''

    def setUp(self):
        '''Set up the test environment.'''
        TarmacTestCase.setUp(self)

        self.bzrdir = os.path.join(os.getcwd(), "bzr")
        os.environ['BZR_HOME'] = self.bzrdir

        self.config = TarmacConfig()
        self.write_config_file()

    def make_two_branches_to_merge(self):
        '''Make two branches, one with revisions to merge.'''
        mock1 = MockLPBranch()
        self.CONFIG_TEMPLATE = CONFIG_TEMPLATE % {
            'url' : 'file://%s' % mock1.temp_dir,
            'temp_log' : mock1.temp_dir + '.log',
            'temp_tree' : mock1.temp_dir
            }
        self.write_config_file()

        a_branch = branch.Branch.create(mock1, self.config, create_tree=True)
        a_branch.commit("Reading, 'riting, 'rithmetic")
        another_branch = branch.Branch.create(MockLPBranch(
            source_branch=a_branch.bzr_branch), self.config, create_tree=True)
        another_branch.commit('ABC...')
        another_branch.commit('...as easy as 123')

        return a_branch, another_branch

    def test_create(self):
        '''Test the creation of a TarmacBranch instance.'''
        mock1 = MockLPBranch()
        self.CONFIG_TEMPLATE = CONFIG_TEMPLATE % {
            'url' : 'file://%s' % mock1.temp_dir,
            'temp_log' : mock1.temp_dir + '.log',
            'temp_tree' : mock1.temp_dir
            }
        self.write_config_file()

        self.assertTrue(self.config.has_section('file://%s' % mock1.temp_dir))
        self.assertEqual(self.config.get('file://%s' % mock1.temp_dir,
                                         'tree_dir', None),
                         mock1.temp_dir)
        a_branch = branch.Branch.create(mock1, self.config)

        self.assertTrue(isinstance(a_branch, branch.Branch))
        self.assertTrue(a_branch.lp_branch.bzr_identity)
        self.assertFalse(hasattr(a_branch, 'tree'))

    def test_create_with_tree(self):
        '''Test the creation of a TarmacBranch with a created tree.'''
        mock1 = MockLPBranch()
        self.CONFIG_TEMPLATE = CONFIG_TEMPLATE % {
            'url' : 'file://%s' % mock1.temp_dir,
            'temp_log' : mock1.temp_dir + '.log',
            'temp_tree' : mock1.temp_dir
            }
        self.write_config_file()

        a_branch = branch.Branch.create(mock1, self.config,
                                        create_tree=True)

        self.assertTrue(isinstance(a_branch, branch.Branch))
        self.assertTrue(a_branch.lp_branch.bzr_identity)
        self.assertTrue(hasattr(a_branch, 'tree'))

    def test_merge_raises_exception_with_no_tree(self):
        '''A merge on a branch with no tree will raise an exception.'''
        a_branch = branch.Branch(MockLPBranch())
        another_branch = branch.Branch(MockLPBranch())

        self.assertRaises(
            AttributeError, a_branch.merge, another_branch)

    def test_merge_no_changes(self):
        '''A merge on a branch with a tree will raise an exception if no
        changes are present.'''
        a_branch = branch.Branch.create(MockLPBranch(), self.config,
                                        create_tree=True)
        another_branch = branch.Branch(MockLPBranch())

        # XXX: Find a way to generate dummy revisions for the second branch.
        self.assertRaises(NoCommits, a_branch.merge, another_branch)

    def test_merge(self):
        '''A merge on a branch with a tree of a branch with changes will merge.
        '''
        a_branch, another_branch = self.make_two_branches_to_merge()
        a_branch.merge(another_branch)
        self.assertTrue(a_branch.has_changes)
        a_branch.lp_branch.cleanup()
        another_branch.lp_branch.cleanup()

    def test_merge_with_authors(self):
        '''A merge from a branch with authors'''
        branch1, branch2 = self.make_two_branches_to_merge()
        authors = [ 'author1', 'author2' ]
        branch1.commit('Authors test', authors=authors)
        branch2.merge(branch1)
        branch2.commit('Authors Merge test', authors=branch1.authors)
        self.assertEqual(branch2.authors.sort(), authors.sort())

    def test_merge_with_bugs(self):
        '''A merge from a branch with authors'''
        branch1, branch2 = self.make_two_branches_to_merge()
        bugs = ['https://launchpad.net/bugs/1 fixed',
                'https://bugzilla.gnome.org/show_bug.cgi?id=1 fixed',
                'https://launchpad.net/bugs/2 fixed'
                ]
        revprops = {}
        revprops['bugs'] = '\n'.join(bugs)
        branch1.commit('Bugs test', revprops)
        branch1.commit('Testing')
        branch2.commit('Foo',
                       revprops={'bugs':'https://launchpad.net/bugs/3 fixed'})
        branch2.merge(branch1)
        self.assertEqual(branch1.fixed_bugs(branch2), [u'1', u'2'])
        branch2.cleanup()

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
        a_branch.lp_branch.cleanup()
        another_branch.lp_branch.cleanup()

    def test_cleanup(self):
        '''The branch object should clean up after itself.'''
        a_branch, another_branch = self.make_two_branches_to_merge()
        a_branch.merge(another_branch)
        self.assertTrue(a_branch.has_changes)

        a_branch.cleanup()
        self.assertTrue(a_branch.has_changes)

        a_branch.lp_branch.cleanup()
        another_branch.lp_branch.cleanup()
