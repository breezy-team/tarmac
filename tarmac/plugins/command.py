# Copyright 2013 Canonical Ltd.
# Copyright 2009 Paul Hummer
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
'''Tarmac plugin for running tests pre-commit.'''

from tempfile import SpooledTemporaryFile, TemporaryDirectory

from breezy.export import export
import os
import subprocess

from tarmac.exceptions import TarmacMergeError, TarmacMergeSkipError
from tarmac.hooks import tarmac_hooks
from tarmac.plugins import TarmacPlugin

# The OUTPUT_TIMEOUT setting (expressed in seconds) affects how long a test
# will run before it is deemed to be hung, and then appropriately terminated.
# It's principal use is preventing a job from hanging indefinitely and backing
# up the queue.
# e.g. Usage: TIMEOUT = 60 * 15
# This will set the timeout to 15 minutes.
OUTPUT_TIMEOUT = 60 * 15

# Maximum run time for any command.
REGULAR_TIMEOUT = 60 * 60


class VerifyCommandFailed(TarmacMergeError):
    """Running the verify_command failed."""


class SetupCommandFailed(TarmacMergeSkipError):
    """Running the setup_command failed."""


def trim_output(output):
    """Trim output so it doesn't exceed launchpad's limits."""
    lines = output.splitlines(True)
    if len(lines) > 3000:
        return ''.join(
            lines[:100]
            + ["\n\n\n... OUTPUT TRIMMED ... \n\n\n"]
            + lines[-100:])
    return output


def killem(pid, signal):
    """Kill the process group leader by pid and other group members

    The command should set it's process to a process group leader.
    """
    import errno
    try:
        os.killpg(os.getpgid(pid), signal)
    except OSError as x:
        if x.errno != errno.ESRCH:
            raise


class NoOutput(Exception):

    def __init__(self, timeout, command, output):
        self.timeout = timeout
        self.command = command
        self.output = output


def run_command_with_output_timeout(
        command, logger, *, timeout=None,
        output_timeout=None, **kwargs):
    import select
    import signal
    import time
    import tempfile

    proc = subprocess.Popen(
        command,
        shell=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        **kwargs)

    start_time = time.time()

    with tempfile.TemporaryFile() as stdout:

        # Do proc.communicate(), but timeout if there's no activity on stdout
        # or stderr for too long.
        open_readers = set([proc.stdout])

        while open_readers:
            elapsed = time.time() - start_time
            if timeout is not None:
                remaining_timeout = max(timeout - elapsed, 0)
            else:
                remaining_timeout = None

            rlist, wlist, xlist = select.select(
                open_readers, [], [],
                min(filter(None, [remaining_timeout, output_timeout])))

            if timeout is not None and elapsed > timeout:
                out_rest = proc.stdout.read()
                stdout.write(out_rest)
                stdout.seek(0)
                raise subprocess.TimeoutExpired(
                    command, timeout, output=stdout.read())

            if len(rlist) == 0:
                if proc.poll() is not None:
                    break

                logger.debug(
                    "Command appears to be hung. There has been no output for"
                    " %d seconds. Sending SIGTERM." % output_timeout)
                killem(proc.pid, signal.SIGTERM)
                time.sleep(5)

                if proc.poll() is not None:
                    logger.debug("SIGTERM did not work. Sending SIGKILL.")
                    killem(proc.pid, signal.SIGKILL)

                # Drain the subprocess's stdout and stderr.
                out_rest = proc.stdout.read()
                stdout.write(out_rest)
                stdout.seek(0)
                raise NoOutput(output_timeout, command, output=stdout.read())

            if proc.stdout in rlist:
                chunk = os.read(proc.stdout.fileno(), 1024)
                if not chunk:
                    open_readers.remove(proc.stdout)
                else:
                    stdout.write(chunk)

        returncode = proc.wait()
        stdout.seek(0)
        if returncode != 0:
            raise subprocess.CalledProcessError(
                returncode, command, output=stdout.read())
        return stdout.read()


class Command(TarmacPlugin):
    '''Tarmac plugin for running a test command.

    This plugin checks for a config setting specific to the project.  If it
    finds one, it will run that command pre-commit.  On fail, it calls the
    do_failed method, and on success, continues.
    '''

    def run(self, command, target, source, proposal):
        self.verify_command = target.config.get('verify_command')
        self.verify_command_output_timeout = int(
            target.config.get('verify_command_output_timeout', OUTPUT_TIMEOUT))
        self.verify_command_timeout = int(
            target.config.get('verify_command_timeout', REGULAR_TIMEOUT))

        if not self.verify_command:
            return

        self.proposal = proposal
        self.setup_command = target.config.get('setup_command')

        cwd = os.getcwd()
        # Export the changes to a temporary directory, and run the command
        # there, to prevent possible abuse of running commands in the tree.
        temp_path = '/tmp/tarmac'
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)
        with TemporaryDirectory(prefix=temp_path + '/branch.') as export_dest:
            export(target.tree, export_dest, per_file_timestamps=False,
                   recurse_nested=True)

            if self.setup_command:
                self.logger.debug('Running setup command: %s',
                                  self.setup_command)
                with SpooledTemporaryFile() as output:
                    try:
                        subprocess.check_call(
                            self.setup_command,
                            shell=True,
                            timeout=REGULAR_TIMEOUT,
                            stdin=subprocess.DEVNULL,
                            stdout=output, stderr=subprocess.STDOUT,
                            cwd=export_dest)
                    except subprocess.TimeoutExpired as e:
                        self.do_setup_failed(
                            'Command timeout out after %d seconds.'
                            % e.timeout, e.output)
                    except subprocess.CalledProcessError as e:
                        self.do_setup_failed(
                            'Command exited with %d' % e.returncode, e.output)

            self.logger.debug('Running test command: %s', self.verify_command)
            with SpooledTemporaryFile() as output:
                try:
                    output = run_command_with_output_timeout(
                        self.verify_command,
                        logger=self.logger,
                        timeout=self.verify_command_timeout,
                        output_timeout=self.verify_command_output_timeout,
                        cwd=export_dest)
                except subprocess.TimeoutExpired as e:
                    self.do_failed(
                        '(``verify_command_timeout``) '
                        'Command ran for more than %d seconds.' % e.timeout,
                        e.output)
                except NoOutput as e:
                    self.do_failed(
                        '(``verify_command_output_timeout``) '
                        'Command sent no output for %d seconds.' % e.timeout,
                        e.output)
                except subprocess.CalledProcessError as e:
                    self.do_failed(
                        'Command exited with %d.' % e.returncode, e.output)

                os.chdir(cwd)
                self.logger.debug(
                    'Completed test command: %s',
                    self.verify_command)

    def do_failed(self, reason, output_value):
        '''Perform failure tests.

        In this case, the output of the test command is posted as a comment,
        and the merge proposal is then set to "Needs review" so that Tarmac
        doesn't attempt to merge it again without human interaction.  An
        exception is then raised to prevent the commit from happening.
        '''
        message = 'Test command "%s" failed: %s' % (
            self.verify_command, reason)
        full_output_value = output_value.decode('UTF-8', 'replace')
        output_value = trim_output(full_output_value)
        comment = ('The attempt to merge %(source)s into %(target)s failed. '
                   '%(reason)s\n'
                   'Below is the output from the failed tests.\n\n'
                   '%(output)s') % {
            'reason': reason,
            'source': self.proposal.source_branch.display_name,
            'target': self.proposal.target_branch.display_name,
            'output': output_value,
            }
        self.logger.info(
            'Output of failed command %s: %s', self.verify_command,
            output_value)
        raise VerifyCommandFailed(message, comment)

    def do_setup_failed(self, reason, output_value):
        '''Perform setup failure tests.
        '''
        message = 'Setup command "%s" failed: %s' % (
            self.setup_command, reason)
        full_output_value = output_value.decode('UTF-8', 'replace')
        output_value = trim_output(full_output_value)
        self.logger.info(
            'Output of failed setup command %s: %s', self.setup_command,
            output_value)
        raise SetupCommandFailed(message, output_value)


tarmac_hooks['tarmac_pre_commit'].hook(Command(), 'Command plugin')
