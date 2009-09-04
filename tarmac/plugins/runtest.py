# Copyright 2009 Paul Hummer
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

'''Tarmac plugin for running tests pre-commit.'''
import os
import subprocess

from bzrlib.errors import HookFailed

from tarmac.hooks import tarmac_hooks
from tarmac.plugins import TarmacPlugin


class RunTest(TarmacPlugin):
    '''Tarmac plugin for running a test command.

    This plugin checks for a config setting specific to the project.  If it
    finds one, it will run that command pre-commit.  On fail, it calls the
    do_failed method, and on success, continues.
    '''
    #TODO: Add the specific config it checks for.
    #TODO: Add the ability to override the test command in the command line.

    def __call__(self, options, configuration, candidate, trunk):

        if options.test_command:
            self.test_command = options.test_command
        elif configuration.test_command:
            self.test_command = configuration.test_command
        else:
            return True

        self.candidate = candidate

        cwd = os.getcwd()
        os.chdir(trunk.tree_dir)
        print 'Running test command: %s' % self.test_command
        proc = subprocess.Popen(
            self.test_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout_value, stderr_value = proc.communicate()
        return_code = proc.wait()
        os.chdir(cwd)

        if return_code == 0:
            return

        else:
            self.do_failed(stdout_value, stderr_value)
            #XXX matsubara: this line will always fail with 
            # IndexError: string index out of range. HookFailed expects a
            # a (exc_type, exc_value, exc_tb) object. Maybe use
            # sys.exc_info() here? See bug 424466
            raise HookFailed('test', 'runtest', '')

    def do_failed(self, stdout_value, stderr_value):
        '''Perform failure tests.

        In this case, the output of the test command is posted as a comment,
        and the merge proposal is then set to "Needs review" so that Tarmac
        doesn't attempt to merge it again without human interaction.  An
        exception is then raised to prevent the commit from happening.
        '''
        comment = (u'The attempt to merge %(source)s into %(target)s failed.' +
                   u'Below is the output from the failed tests.\n\n' +
                   u'%(output)s') % {
            'source' : self.candidate.source_branch.display_name,
            'target' : self.candidate.target_branch.display_name,
            'output' : u'\n'.join([stdout_value, stderr_value]),
            }
        subject = u'Re: [Merge] %s into %s' % (
            self.candidate.source_branch.display_name,
            self.candidate.target_branch.display_name)
        self.candidate.createComment(subject=subject, content=comment)
        self.candidate.setStatus(status=u'Needs review')
        self.candidate.lp_save()


tarmac_hooks['pre_tarmac_commit'].hook(RunTest(), 'Test run hook')
