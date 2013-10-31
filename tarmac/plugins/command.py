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

# Head off lint warnings.
errno = None
os = None
select = None
shutil = None
signal = None
subprocess = None
sys = None
tempfile = None
time = None

# The TIMEOUT setting (expressed in seconds) affects how long a test will run
# before it is deemed to be hung, and then appropriately terminated.
# It's principal use is preventing a job from hanging indefinitely and
# backing up the queue.
# e.g. Usage: TIMEOUT = 60 * 15
# This will set the timeout to 15 minutes.
TIMEOUT = 60 * 15

from bzrlib.export import export
from bzrlib.lazy_import import lazy_import
lazy_import(globals(), '''
    import errno
    import os
    import select
    import shutil
    import signal
    import subprocess
    import sys
    import tempfile
    import time
    ''')

from tarmac.exceptions import TarmacMergeError
from tarmac.hooks import tarmac_hooks
from tarmac.plugins import TarmacPlugin


def killem(pid, signal):
    """
    Kill the process group leader identified by pid and other group members

    The verify_command should set it's process to a process group leader.
    """
    try:
        os.killpg(os.getpgid(pid), signal)
    except OSError, x:
        if x.errno == errno.ESRCH:
            pass
        else:
            raise


class VerifyCommandFailed(TarmacMergeError):
    """Running the verify_command failed."""


class Command(TarmacPlugin):
    '''Tarmac plugin for running a test command.

    This plugin checks for a config setting specific to the project.  If it
    finds one, it will run that command pre-commit.  On fail, it calls the
    do_failed method, and on success, continues.
    '''

    def run(self, command, target, source, proposal):
        try:
            self.verify_command = target.config.verify_command
        except AttributeError:
            # This can be killed two versions after 0.4, whatever version that
            # is.
            try:
                self.verify_command = target.config.test_command
                self.logger.warn(
                    'test_command config setting is deprecated. '
                    'Please use verify_command instead.')
            except AttributeError:
                return

        self.proposal = proposal

        self.logger.debug('Running test command: %s' % self.verify_command)
        cwd = os.getcwd()
        # Export the changes to a temporary directory, and run the command
        # there, to prevent possible abuse of running commands in the tree.
        temp_path = '/tmp/tarmac'
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)
        export_dest = tempfile.mkdtemp(prefix=temp_path + '/branch.')
        export(target.tree, export_dest, None, None, None, filtered=False,
               per_file_timestamps=False)
        os.chdir(export_dest)

        proc = subprocess.Popen(self.verify_command,
                                shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        proc.stdin.close()
        stdout = tempfile.TemporaryFile()
        stderr = tempfile.TemporaryFile()

        # Do proc.communicate(), but timeout if there's no activity on stdout or
        # stderr for too long.
        open_readers = set([proc.stdout, proc.stderr])

        while open_readers:
            rlist, wlist, xlist = select.select(open_readers, [], [], TIMEOUT)

            if len(rlist) == 0:
                if proc.poll() is not None:
                    break

                self.logger.debug(
                    "Command appears to be hung. There has been no output for"
                    " %d seconds. Sending SIGTERM." % TIMEOUT)
                killem(proc.pid, signal.SIGTERM)
                time.sleep(5)

                if proc.poll() is not None:
                    self.logger.debug("SIGTERM did not work. Sending SIGKILL.")
                    killem(proc.pid, signal.SIGKILL)

                # Drain the subprocess's stdout and stderr.
                out_rest = proc.stdout.read()
                if command.config.debug:
                    sys.stdout.write(out_rest)
                stdout.write(out_rest)

                err_rest = proc.stderr.read()
                if command.config.debug:
                    sys.stderr.write(err_rest)
                stderr.write(err_rest)
                break

            if proc.stdout in rlist:
                chunk = os.read(proc.stdout.fileno(), 1024)
                if chunk == "":
                    open_readers.remove(proc.stdout)
                else:
                    if command.config.debug:
                        sys.stdout.write(chunk)
                    stdout.write(chunk)
                    
            if proc.stderr in rlist:
                chunk = os.read(proc.stderr.fileno(), 1024)
                if chunk == "":
                    open_readers.remove(proc.stderr)
                else:
                    if command.config.debug:
                        sys.stderr.write(chunk)
                    stderr.write(chunk)

        return_code = proc.wait()

        os.chdir(cwd)
        shutil.rmtree(export_dest)
        self.logger.debug('Completed test command: %s' % self.verify_command)

        stdout.seek(0)
        stderr.seek(0)

        if return_code != 0:
            self.do_failed(stdout.read(), stderr.read())

    def do_failed(self, stdout_value, stderr_value):
        '''Perform failure tests.

        In this case, the output of the test command is posted as a comment,
        and the merge proposal is then set to "Needs review" so that Tarmac
        doesn't attempt to merge it again without human interaction.  An
        exception is then raised to prevent the commit from happening.
        '''
        message = u'Test command "%s" failed.' % self.verify_command
        stdout_value = stdout_value.decode('UTF-8', 'replace')
        stderr_value = stderr_value.decode('UTF-8', 'replace')
        comment = (u'The attempt to merge %(source)s into %(target)s failed. '
                   u'Below is the output from the failed tests.\n\n'
                   u'%(output)s') % {
            'source': self.proposal.source_branch.display_name,
            'target': self.proposal.target_branch.display_name,
            'output': u'\n'.join([stdout_value, stderr_value]),
            }
        raise VerifyCommandFailed(message, comment)


tarmac_hooks['tarmac_pre_commit'].hook(Command(), 'Command plugin')
