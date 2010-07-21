'''Tests for tarmac.bin.commands.py.'''
from cStringIO import StringIO
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
        if not config:
            raise Exception('No config provided.')
        else:
            self.config = config

        for section in self.config.sections():
            if section == 'Tarmac':
                continue
            else:
                print 'Merging %(branch)s' % {'branch' : section}


class TestCommand(TarmacTestCase):
    '''Test for tarmac.bin.commands.Command.'''

    def test__init__(self):
        registry = CommandRegistry()
        command_name = u'test'
        command = commands.TarmacCommand(registry)
        command.NAME = command_name
        self.assertEqual(command.NAME, command_name)
        self.assertTrue(isinstance(command.config, TarmacConfig))

    def test_run(self):
        registry = CommandRegistry()
        command = commands.TarmacCommand(registry)
        self.assertRaises(NotImplementedError, command.run)


class TestAuthCommand(TarmacTestCase):
    '''Test for tarmac.bin.command.cmd_auth.'''

    NEEDS_SAMPLE_DATA = True

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
        tmp_stderr = StringIO()
        old_stderr = sys.stderr
        sys.stderr = tmp_stderr

        registry = CommandRegistry()
        registry.register_command('authenticate', commands.cmd_authenticate)
        command = registry._get_command(commands.cmd_authenticate,
                                        'authenticate')
        command.run()
        self.assertEqual(
            tmp_stderr.getvalue(),
            'You have already been authenticated.\n')

        sys.stderr = old_stderr


class TestHelpCommand(TarmacTestCase):

    def test_run(self):
        tmp_stdout = StringIO()
        old_stdout = sys.stdout
        sys.stdout = tmp_stdout

        registry = CommandRegistry()
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

    NEEDS_SAMPLE_DATA = True

    def test_run(self):
        tmp_stdout = StringIO()
        old_stdout = sys.stdout
        sys.stdout = tmp_stdout

        config = TarmacConfig()
        self.write_config_file(config)

        registry = CommandRegistry()
        registry.register_command('merge', commands.cmd_merge)
        command = registry._get_command(commands.cmd_merge, 'merge')
        command.run(launchpad=FakeLaunchpad(config=config))
        self.assertEqual(
            tmp_stdout.getvalue(),
            'Merging lp:~tarmac/tarmac/tarmac\n'
            'Merging lp:~tarmac/tarmac/tarmac3\n'
            'Merging lp:~tarmac/tarmac/tarmac2\n'
            'Merging lp:~tarmac/tarmac/tarmac4\n')

        sys.stdout = old_stdout
