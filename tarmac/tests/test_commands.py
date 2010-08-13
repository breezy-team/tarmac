'''Tests for tarmac.bin.commands.py.'''
from cStringIO import StringIO
import os
import sys

from tarmac.bin import commands
from tarmac.bin.registry import CommandRegistry
from tarmac.config import TarmacConfig
from tarmac.tests import TarmacTestCase


class FakeCommand(commands.TarmacCommand):
    '''Fake command for testing.'''

    def get_help_text(self):
        return 'You need help.\n'

    def run(self, *args, **kwargs):
        return


class FakeLaunchpad(object):
    '''Fake Launchpad object for testing.'''

    def __init__(self, config=None, *args, **kwargs):
        """Fake Launchpad object."""


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


class TestMergeCommand(TarmacTestCase):

    def test_run(self):
        tmp_stdout = StringIO()
        old_stdout = sys.stdout
        sys.stdout = tmp_stdout

        def _do_merges(branch_url, *args, **kwargs):
            """Just checking."""
            print 'Merging %s' % branch_url

        branches = ['lp:foo', 'lp:bar', 'lp:baz']
        for branch in branches:
            self.config.add_section(branch)

        registry = CommandRegistry(config=self.config)
        registry.register_command('merge', commands.cmd_merge)

        command = registry._get_command(commands.cmd_merge, 'merge')
        command._do_merges = _do_merges
        command.run(launchpad=FakeLaunchpad())
        self.assertEqual(tmp_stdout.getvalue(),
                         '\n'.join(
                ['Merging %s' % b for b in  sorted(branches, reverse=True)]
                ) + '\n')

        for branch in branches:
            self.config.remove_section(branch)

        sys.stdout = old_stdout
