'''Tests for tarmac.bin.commands.py.'''
from cStringIO import StringIO
import sys

from tarmac.bin import commands
from tarmac.bin.registry import CommandRegistry
from tarmac.config import TarmacConfig
from tarmac.exceptions import UnapprovedChanges
from tarmac.tests import TarmacTestCase, BranchTestCase
from tarmac.tests.mock import Thing


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
        '''If the user has already been authenticated, don't try again.'''
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
                name='source',
                revision_count=self.branch2.lp_branch.revision_count,
                landing_candidates=[]),
                         Thing(
                bzr_identity=self.branch1.lp_branch.bzr_identity,
                display_name=self.branch1.lp_branch.bzr_identity,
                name='target',
                revision_count=self.branch1.lp_branch.revision_count,
                landing_candidates=None)]
        self.proposals = [Thing(self_link=u'',
                                queue_status=u'Needs Review',
                                commit_message=u'Commitable.',
                                source_branch=self.branches[0],
                                target_branch=self.branches[1],
                                createComment=self.createComment,
                                setStatus=self.lp_save,
                                lp_save=self.lp_save,
                                reviewed_revid=None,
                                votes=[Thing(
                        comment=Thing(vote=u'Needs Fixing'),
                        reviewer=Thing(display_name=u'Reviewer'))]),
                          Thing(self_link=u'',
                                queue_status=u'Approved',
                                commit_message=u'Commit this.',
                                source_branch=self.branches[0],
                                target_branch=self.branches[1],
                                createComment=self.createComment,
                                setStatus=self.lp_save,
                                lp_save=self.lp_save,
                                reviewed_revid=None,
                                votes=[Thing(
                        comment=Thing(vote=u'Approved'),
                        reviewer=Thing(display_name=u'Reviewer'))])]
        self.branches[1].landing_candidates = self.proposals

        self.launchpad = Thing(branches=Thing(getByUrl=self.getBranchByUrl))
        self.error = None

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
        self.proposals[1].reviewed_revid = \
            self.branch2.bzr_branch.last_revision()
        registry = CommandRegistry(config=self.config)
        registry.register_command('merge', commands.cmd_merge)

        command = registry._get_command(commands.cmd_merge, 'merge')
        command.run(launchpad=self.launchpad)

    def test_run_unapprovedchanges(self):
        self.proposals[1].reviewed_revid = \
            self.branch2.bzr_branch.dotted_revno_to_revision_id(
            (self.branch2.bzr_branch.revno() - 1,))
        registry = CommandRegistry(config=self.config)
        registry.register_command('merge', commands.cmd_merge)

        command = registry._get_command(commands.cmd_merge, 'merge')
        command.run(launchpad=self.launchpad)
        self.assertTrue(isinstance(self.error, UnapprovedChanges))

    def test_run_no_reviewed_revid(self):
        self.proposals[1].reviewed_revid = None
        registry = CommandRegistry(config=self.config)
        registry.register_command('merge', commands.cmd_merge)

        command = registry._get_command(commands.cmd_merge, 'merge')
        command.run(launchpad=self.launchpad)
        self.assertTrue(isinstance(self.error, UnapprovedChanges))
        self.assertEqual(self.error.comment,
                         u'No approved revision specified.')
