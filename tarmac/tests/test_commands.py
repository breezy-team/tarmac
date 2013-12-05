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
'''Tests for tarmac.bin.commands.py.'''
from cStringIO import StringIO
import os
import shutil
import sys

from mock import patch
from tarmac.bin import commands
from tarmac.bin.registry import CommandRegistry
from tarmac.branch import Branch
from tarmac.config import TarmacConfig
from tarmac.exceptions import (
    InvalidWorkingTree,
    UnapprovedChanges,
)
from tarmac.tests import (
    BranchTestCase,
    MockLPBranch,
    TarmacTestCase,
    Thing,
)


class FakeCommand(commands.TarmacCommand):
    '''Fake command for testing.'''

    def get_help_text(self):
        return 'You need help.\n'

    def run(self, *args, **kwargs):
        return


class TestCommand(TarmacTestCase):
    '''Test for tarmac.bin.commands.Command.'''

    def test__init__(self):
        registry = CommandRegistry(config=self.config)
        command_name = u'test'
        command = commands.TarmacCommand(registry)
        command.NAME = command_name
        self.assertEqual(command.NAME, command_name)
        self.assertTrue(isinstance(command.config, TarmacConfig))

    def test_run(self):
        registry = CommandRegistry(config=self.config)
        command = commands.TarmacCommand(registry)
        command.run()


class TestAuthCommand(TarmacTestCase):
    '''Test for tarmac.bin.command.cmd_auth.'''

    # XXX: rockstar - 10 Jan 2010 - How do I test this with the OAuth request,
    # etc?
    #def test_run(self):
    #    '''Test that calling the auth command gets a Lanuchpad token.'''

    #    tmp_stdout = StringIO()
    #    old_stdout = sys.stdout
    #    sys.stdout = tmp_stdout

    #    command = cmd_auth()
    #    self.assertFalse(os.path.exists(command.config.CREDENTIALS))
    #    command.run()
    #    self.assertEqual(tmp_stdout.getvalue(), '')

    #    sys.stdout = old_stdout

    def test_run_already_authenticated(self):
        '''If the user has already been authenticated, do not try again.'''
        registry = CommandRegistry(config=self.config)
        registry.register_command('authenticate', commands.cmd_authenticate)
        command = registry._get_command(commands.cmd_authenticate,
                                        'authenticate')

        def fail_if_get_lp_object(*args, **kwargs):
            '''Fail if get_launchpad_object is called here.'''
            raise Exception('Not already authenticated.')

        command.get_launchpad_object = fail_if_get_lp_object
        command.run()


class TestHelpCommand(TarmacTestCase):

    def test_run(self):
        tmp_stdout = StringIO()
        old_stdout = sys.stdout
        sys.stdout = tmp_stdout

        registry = CommandRegistry(config=self.config)
        registry.register_command('foo', FakeCommand)

        registry.register_command('help', commands.cmd_help)
        command = registry._get_command(commands.cmd_help, 'help')
        command.outf = tmp_stdout
        command.run(command='foo')
        self.assertEqual(
            tmp_stdout.getvalue(),
            'You need help.\n')

        sys.stdout = old_stdout


class TestMergeCommand(BranchTestCase):

    def setUp(self):
        super(TestMergeCommand, self).setUp()

        self.branches = [Thing(
                bzr_identity=self.branch2.lp_branch.bzr_identity,
                display_name=self.branch2.lp_branch.bzr_identity,
                web_link=self.branch2.lp_branch.bzr_identity,
                name='source',
                unique_name='source',
                revision_count=self.branch2.lp_branch.revision_count,
                landing_candidates=[],
                landing_targets=[]),
                         Thing(
                bzr_identity=self.branch1.lp_branch.bzr_identity,
                display_name=self.branch1.lp_branch.bzr_identity,
                web_link=self.branch1.lp_branch.bzr_identity,
                name='target',
                unique_name='target',
                revision_count=self.branch1.lp_branch.revision_count,
                landing_candidates=None)]
        self.proposals = [Thing(
                self_link=u'http://api.edge.launchpad.net/devel/proposal0',
                web_link=u'http://api.edge.launchpad.net/devel/proposal0',
                queue_status=u'Needs Review',
                commit_message=u'Commitable.',
                source_branch=self.branches[0],
                target_branch=self.branches[1],
                prerequisite_branch=None,
                createComment=self.createComment,
                setStatus=self.lp_save,
                lp_save=self.lp_save,
                reviewed_revid=None,
                votes=[Thing(
                        comment=Thing(vote=u'Needs Fixing'),
                        reviewer=Thing(display_name=u'Reviewer'))]),
                          Thing(
                self_link=u'https://api.launchpad.net/1.0/proposal1',
                web_link=u'https://api.launchpad.net/1.0/proposal1',
                queue_status=u'Approved',
                commit_message=u'Commit this.',
                source_branch=self.branches[0],
                target_branch=self.branches[1],
                prerequisite_branch=None,
                createComment=self.createComment,
                setStatus=self.lp_save,
                lp_save=self.lp_save,
                reviewed_revid=None,
                votes=[Thing(
                        comment=Thing(vote=u'Approve'),
                        reviewer=Thing(display_name=u'Reviewer')),
                                       Thing(
                        comment=Thing(vote=u'Abstain'),
                        reviewer=Thing(display_name=u'Reviewer2'))])]
        self.branches[1].landing_candidates = self.proposals
        self.branches[0].landing_targets = [
                self.proposals[0], self.proposals[1]]

        self.launchpad = Thing(branches=Thing(getByUrl=self.getBranchByUrl),
                               me=Thing(display_name='Tarmac'))
        self.error = None
        registry = CommandRegistry(config=self.config)
        registry.register_command('merge', commands.cmd_merge)

        self.command = registry._get_command(commands.cmd_merge, 'merge')

    def addProposal(self, name, prerequisite_branch=None):
        """Create a 3rd branch with a proposal"""
        # Create a 3rd branch we'll use to test with
        branch3_dir = os.path.join(self.TEST_ROOT, name)
        mock3 = MockLPBranch(branch3_dir, source_branch=self.branch1.lp_branch)
        branch3 = Branch.create(mock3, self.config, create_tree=True,
                                target=self.branch1)
        branch3.commit('Prerequisite commit.')
        branch3.lp_branch.revision_count += 1

        # Set up an approved proposal for the branch (prereq on branches[0])
        branch3.lp_branch.display_name = branch3.lp_branch.bzr_identity
        branch3.lp_branch.name = name
        branch3.lp_branch.unique_name = '~user/branch/' + name
        branch3.lp_branch.landing_candidates = []
        b3_proposal = Thing(
            self_link=u'http://api.edge.launchpad.net/devel/proposal3',
            web_link=u'http://edge.launchpad.net/proposal3',
            queue_status=u'Approved',
            commit_message=u'Commitable.',
            source_branch=branch3.lp_branch,
            target_branch=self.branches[1],
            prerequisite_branch=prerequisite_branch,
            createComment=self.createComment,
            setStatus=self.lp_save,
            lp_save=self.lp_save,
            reviewed_revid=None,
            votes=[Thing(
                    comment=Thing(vote=u'Approve'),
                    reviewer=Thing(display_name=u'Reviewer'))])

        branch3.lp_branch.landing_targets = [b3_proposal]
        self.proposals.append(b3_proposal)
        self.branches.append(branch3.lp_branch)


    def lp_save(self, *args, **kwargs):
        """Do nothing here."""
        pass

    def createComment(self, subject=None, content=None):
        """Fake createComment method for proposals."""
        self.error = UnapprovedChanges(subject, content)

    def getBranchByUrl(self, url=None):
        """Fake method to get branches matching a URL."""
        try:
            return [x for x in self.branches if x.bzr_identity == url][0]
        except IndexError:
            return None

    def test_run(self):
        """Test that the merge command merges a branch successfully."""
        self.proposals[1].reviewed_revid = \
            self.branch2.bzr_branch.last_revision()
        self.command.run(launchpad=self.launchpad)

    def test_run_unapprovedchanges(self):
        """Test that a mismatch between approved and tip raises an error."""
        self.proposals[1].reviewed_revid = \
            self.branch2.bzr_branch.dotted_revno_to_revision_id(
            (self.branch2.bzr_branch.revno() - 1,))
        self.command.run(launchpad=self.launchpad)
        self.assertTrue(isinstance(self.error, UnapprovedChanges))

    def test_run_no_reviewed_revid(self):
        """Test that no reviewed revid raises an error."""
        self.proposals[1].reviewed_revid = None
        self.command.run(launchpad=self.launchpad)
        self.assertTrue(isinstance(self.error, UnapprovedChanges))
        self.assertEqual(self.error.comment,
                         u'No approved revision specified.')

    def test_get_reviews(self):
        """Test that the _get_reviews method gives the right lists."""
        self.assertEqual(self.command._get_reviews(self.proposals[0]),
                         [u'Reviewer;Needs Fixing'])
        self.assertEqual(self.command._get_reviews(self.proposals[1]),
                         [u'Reviewer;Approve', u'Reviewer2;Abstain'])

    def test_run_merge_url_substitution(self):
        """Test that the merge urls get substituted correctly."""
        self.proposals[1].reviewed_revid = \
            self.branch2.bzr_branch.last_revision()
        self.command.run(launchpad=self.launchpad)
        revid = self.branch1.bzr_branch.last_revision()
        last_rev = self.branch1.bzr_branch.repository.get_revision(revid)
        self.assertEqual(last_rev.properties.get('merge_url', None),
                         u'http://code.launchpad.net/proposal1')

        # This proposal merged ok
        self.proposals[1].queue_status = u'Merged'

        # Make a new commit, approve the propsoal, merge, and verify
        self.branch2.commit('New commit to merge.')
        self.proposals[0].queue_status = u'Approved'
        self.proposals[0].reviewed_revid = \
            self.branch2.bzr_branch.last_revision()
        self.command.run(launchpad=self.launchpad)
        revid = self.branch1.bzr_branch.last_revision()
        last_rev = self.branch1.bzr_branch.repository.get_revision(revid)
        self.assertEqual(last_rev.properties.get('merge_url', None),
                         u'http://code.launchpad.net/proposal0')

    def test_run_merge_with_unmerged_prerequisite_skips(self):
        """Test that mereging a branch with an unmerged prerequisite skips."""
        # Create a 3rd prerequisite branch we'll use to test with
        branch3_dir = os.path.join(self.TEST_ROOT, 'branch3')
        mock3 = MockLPBranch(branch3_dir, source_branch=self.branch1.lp_branch)
        branch3 = Branch.create(mock3, self.config, create_tree=True,
                                target=self.branch1)
        branch3.commit('Prerequisite commit.')
        branch3.lp_branch.revision_count += 1

        # Merge the prerequisite and create another commit after
        self.branch2.merge(branch3)
        self.branch2.commit('Merged prerequisite.')
        self.branch2.commit('Post-merge commit.')
        self.branch2.lp_branch.revision_count += 2

        # Set up an unapproved proposal for the prerequisite
        branch3.lp_branch.display_name = branch3.lp_branch.bzr_identity
        branch3.lp_branch.name = 'branch3'
        branch3.unique_name = 'branch3'
        branch3.lp_branch.landing_candidates = []
        b3_proposal = Thing(
            self_link=u'http://api.edge.launchpad.net/devel/proposal3',
            web_link=u'http://api.edge.launchpad.net/devel/proposal3',
            queue_status=u'Work in Progress',
            commit_message=u'Commitable.',
            source_branch=branch3.lp_branch,
            target_branch=self.branches[1],
            prerequisite_branch=None,
            createComment=self.createComment,
            setStatus=self.lp_save,
            lp_save=self.lp_save,
            reviewed_revid=None,
            votes=[Thing(
                    comment=Thing(vote=u'Needs Fixing'),
                    reviewer=Thing(display_name=u'Reviewer'))])

        branch3.lp_branch.landing_targets = [b3_proposal]

        self.proposals.append(b3_proposal)
        self.proposals[1].prerequisite_branch = branch3.lp_branch
        self.proposals[1].reviewed_revid = \
            self.branch2.bzr_branch.last_revision()
        self.assertEqual(self.command.run(launchpad=self.launchpad), None)
        shutil.rmtree(branch3_dir)

    def test_run_merge_with_unproposed_prerequisite_fails(self):
        """Test that mereging a branch with an unmerged prerequisite fails."""
        # Create a 3rd prerequisite branch we'll use to test with
        branch3_dir = os.path.join(self.TEST_ROOT, 'branch-prereq-fails')
        mock3 = MockLPBranch(branch3_dir, source_branch=self.branch1.lp_branch)
        branch3 = Branch.create(mock3, self.config, create_tree=True,
                                target=self.branch1)
        branch3.commit('Prerequisite commit.')
        branch3.lp_branch.revision_count += 1

        # Merge the prerequisite and create another commit after
        self.branch2.merge(branch3)
        self.branch2.commit('Merged prerequisite.')
        self.branch2.commit('Post-merge commit.')
        self.branch2.lp_branch.revision_count += 2

        # Set up an unapproved proposal for the prerequisite
        branch3.lp_branch.display_name = branch3.lp_branch.bzr_identity
        branch3.lp_branch.name = 'branch-prereq-fails'
        branch3.lp_branch.unique_name = 'branch-prereq-fails'
        branch3.lp_branch.landing_candidates = []
        b3_proposal = Thing(
            self_link=u'http://api.edge.launchpad.net/devel/proposal3',
            web_link=u'http://api.edge.launchpad.net/devel/proposal3',
            queue_status=u'Work in Progress',
            commit_message=u'Commitable.',
            source_branch=branch3.lp_branch,
            target_branch=self.branches[1],
            prerequisite_branch=None,
            createComment=self.createComment,
            setStatus=self.lp_save,
            lp_save=self.lp_save,
            reviewed_revid=None,
            votes=[Thing(
                    comment=Thing(vote=u'Needs Fixing'),
                    reviewer=Thing(display_name=u'Reviewer'))])

        branch3.lp_branch.landing_targets = []

        self.proposals.append(b3_proposal)
        self.proposals[1].prerequisite_branch = branch3.lp_branch
        self.proposals[1].reviewed_revid = \
            self.branch2.bzr_branch.last_revision()
        self.command.run(launchpad=self.launchpad)
        shutil.rmtree(branch3_dir)
        self.assertEqual(self.error.comment,
                         u'No proposals found for merge of lp:branch-prereq-fails '
                         u'into lp:branch1.')

    def test_run_merge_with_prerequisite_with_multiple_proposals_fails(self):
        """Test that mereging a branch with an unmerged prerequisite fails."""
        # Create a 3rd prerequisite branch we'll use to test with
        branch3_dir = os.path.join(self.TEST_ROOT, 'branch-proposals-fails')
        mock3 = MockLPBranch(branch3_dir, source_branch=self.branch1.lp_branch)
        branch3 = Branch.create(mock3, self.config, create_tree=True,
                                target=self.branch1)
        branch3.commit('Prerequisite commit.')
        branch3.lp_branch.revision_count += 1

        # Merge the prerequisite and create another commit after
        self.branch2.merge(branch3)
        self.branch2.commit('Merged prerequisite.')
        self.branch2.commit('Post-merge commit.')
        self.branch2.lp_branch.revision_count += 2

        # Set up an unapproved proposal for the prerequisite
        branch3.lp_branch.display_name = branch3.lp_branch.bzr_identity
        branch3.lp_branch.name = 'branch-proposals-fails'
        branch3.lp_branch.unique_name = 'branch-proposals-fails'
        branch3.lp_branch.landing_candidates = []
        b3_proposal = Thing(
            self_link=u'http://api.edge.launchpad.net/devel/proposal3',
            web_link=u'http://api.edge.launchpad.net/devel/proposal3',
            queue_status=u'Work in Progress',
            commit_message=u'Commitable.',
            source_branch=branch3.lp_branch,
            target_branch=self.branches[1],
            prerequisite_branch=None,
            createComment=self.createComment,
            setStatus=self.lp_save,
            lp_save=self.lp_save,
            reviewed_revid=None,
            votes=[Thing(
                    comment=Thing(vote=u'Needs Fixing'),
                    reviewer=Thing(display_name=u'Reviewer'))])

        branch3.lp_branch.landing_targets = [
            b3_proposal,
            Thing(
                target_branch=self.branches[1],
                queue_status='Needs Review')]

        self.proposals.append(b3_proposal)
        self.proposals[1].prerequisite_branch = branch3.lp_branch
        self.proposals[1].reviewed_revid = \
            self.branch2.bzr_branch.last_revision()
        self.command.run(launchpad=self.launchpad)
        shutil.rmtree(branch3_dir)
        self.assertEqual(self.error.comment,
                         u'More than one proposal found for merge of '
                         u'lp:branch-proposals-fails into lp:branch1, '
                         u'which is not Superseded.')

    @patch('bzrlib.workingtree.WorkingTree.open')
    def test_run_merge_with_invalid_workingtree(self, mocked):
        """Test that InvalidWorkingTree is handled correctly."""
        invalid_tree_comment = 'This tree is invalid.'
        mocked.side_effect = InvalidWorkingTree(invalid_tree_comment)
        self.proposals[1].reviewed_revid = \
            self.branch2.bzr_branch.last_revision()
        self.command.run(launchpad=self.launchpad)
        self.assertEqual(self.error.comment,
                         invalid_tree_comment)

    def test__compare_proposals(self):
        """
        _compare_proposals is meant to be a sort routine comparison function
        """
        self.addProposal("compare_proposals", self.branches[0])
        self.assertEqual(
            commands._compare_proposals(self.proposals[0], self.proposals[1]),
            0)
        self.assertEqual(
            commands._compare_proposals(self.proposals[0], self.proposals[2]),
            -1)
        self.assertEqual(
            commands._compare_proposals(self.proposals[2], self.proposals[0]),
            1)

    def test__get_mergable_proposals_for_branch_are_sorted(self):
        """
        Mergable proposals should be in sorted order (prereqs should come
        first in the list)
        """
        self.addProposal("sorted_test", self.branches[0])
        proposals = self.command._get_mergable_proposals_for_branch(
                self.branches[1])
        self.assertEqual(len(proposals), 2)
        self.assertTrue(proposals[1].source_branch.name == "sorted_test")

    def test__get_mergable_proposals_for_branch_prereq_unmerged(self):
        """
        skip mergable proposals that have specified a prereq,
        but that prereq is not merged yet.  This is edge-casey, since
        we now process the queue in an order that makes sense for
        prereqs
        """
        self.addProposal("unmerged")
        self.proposals[0].prerequisite_branch = self.branches[2]
        self.proposals[1].prerequisite_branch = self.branches[2]
        proposals = self.command._get_mergable_proposals_for_branch(
                self.branches[1])
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].source_branch.name, "unmerged")

    def test__get_prerequisite_proposals_no_prerequisites(self):
        """proposals[0] does not have a prerequisite branch listed"""
        proposals = self.command._get_prerequisite_proposals(self.proposals[0])
        self.assertEqual(len(proposals), 0)

    def test__get_prerequisite_proposals_one_prerequisite(self):
        """Branches[0] (source) has two open MPs against it"""
        self.addProposal("one_prerequisite", self.branches[0])
        proposals = self.command._get_prerequisite_proposals(self.proposals[2])
        self.assertEqual(len(proposals), 2)
