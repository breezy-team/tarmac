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

# The TIMEOUT setting (expressed in seconds) affects how long a test will run
# before it is deemed to be hung, and then appropriately terminated.
# It's principal use is preventing a job from hanging indefinitely and
# backing up the queue.
# e.g. Usage: TIMEOUT = 60 * 15
# This will set the timeout to 15 minutes.
TIMEOUT = 60 * 15


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
            + lines[:-100])
    return output


class Command(TarmacPlugin):
    '''Tarmac plugin for running a test command.

    This plugin checks for a config setting specific to the project.  If it
    finds one, it will run that command pre-commit.  On fail, it calls the
    do_failed method, and on success, continues.
    '''

    def run(self, command, target, source, proposal):
        self.verify_command = target.config.get('verify_command')

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
                        return_code = subprocess.check_call(
                            self.setup_command, shell=True,
                            stdin=subprocess.DEVNULL,
                            stdout=output, stderr=output, timeout=TIMEOUT,
                            cwd=export_dest)
                    except subprocess.TimeoutExpired:
                        self.logger.debug(
                            "Setup command appears to be hung. "
                            "There has been no output for"
                            " %d seconds. Sending SIGTERM." % TIMEOUT)
                        output.seek(0)
                        self.do_setup_failed(output.read())
                    except subprocess.CalledProcessError as e:
                        self.logger.debug(
                            "Setup command failed with code %d. ",
                            e.returncode)
                        output.seek(0)
                        self.do_setup_failed(output.read())

            self.logger.debug('Running test command: %s', self.verify_command)
            with SpooledTemporaryFile() as output:
                try:
                    return_code = subprocess.call(
                        self.verify_command, shell=True,
                        stdin=subprocess.DEVNULL,
                        stdout=output, stderr=output, timeout=TIMEOUT,
                        cwd=export_dest)
                except subprocess.TimeoutExpired:
                    self.logger.debug(
                        "Command appears to be hung. "
                        "There has been no output for"
                        " %d seconds. Sending SIGTERM." % TIMEOUT)
                    output.seek(0)
                    self.do_failed(output.read())

                os.chdir(cwd)
                self.logger.debug(
                    'Completed test command: %s',
                    self.verify_command)

                if return_code != 0:
                    output.seek(0)
                    self.do_failed(output.read())

    def do_failed(self, output_value):
        '''Perform failure tests.

        In this case, the output of the test command is posted as a comment,
        and the merge proposal is then set to "Needs review" so that Tarmac
        doesn't attempt to merge it again without human interaction.  An
        exception is then raised to prevent the commit from happening.
        '''
        message = 'Test command "%s" failed.' % self.verify_command
        full_output_value = output_value.decode('UTF-8', 'replace')
        output_value = trim_output(full_output_value)
        comment = ('The attempt to merge %(source)s into %(target)s failed. '
                   'Below is the output from the failed tests.\n\n'
                   '%(output)s') % {
            'source': self.proposal.source_branch.display_name,
            'target': self.proposal.target_branch.display_name,
            'output': output_value,
            }
        self.logger.info(
            'Output of failed command %s: %s', self.verify_command,
            output_value)
        raise VerifyCommandFailed(message, comment)

    def do_setup_failed(self, output_value):
        '''Perform setup failure tests.
        '''
        message = 'Setup command "%s" failed.' % self.setup_command
        full_output_value = output_value.decode('UTF-8', 'replace')
        output_value = trim_output(full_output_value)
        self.logger.info(
            'Output of failed setup command %s: %s', self.setup_command,
            output_value)
        raise SetupCommandFailed(message, output_value)


tarmac_hooks['tarmac_pre_commit'].hook(Command(), 'Command plugin')
