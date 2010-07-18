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

from bzrlib.errors import TipChangeRejected

from tarmac.hooks import tarmac_hooks
from tarmac.plugins import TarmacPlugin


class Command(TarmacPlugin):
    '''Tarmac plugin for running a test command.

    This plugin checks for a config setting specific to the project.  If it
    finds one, it will run that command pre-commit.  On fail, it calls the
    do_failed method, and on success, continues.
    '''

    def __call__(self, command, target, source, proposal):
        try:
            self.verify_command = target.config.verify_command
        except AttributeError:
            return True

        self.proposal = proposal

        cwd = os.getcwd()
        os.chdir(target.config.tree_dir)
        self.logger.debug('Running test command: %s' % self.verify_command)
        proc = subprocess.Popen(
            self.test_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        self.logger.debug('Completed test command: %s' % self.test_command)
        stdout_value, stderr_value = proc.communicate()
        return_code = proc.wait()
        os.chdir(cwd)

        if return_code != 0:
            self.do_failed(stdout_value, stderr_value)
            raise TipChangeRejected(
                'Test command "%s" failed' % self.test_command)

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
            'source' : self.proposal.source_branch.display_name,
            'target' : self.proposal.target_branch.display_name,
            'output' : u'\n'.join([stdout_value, stderr_value]),
            }
        subject = u'Re: [Merge] %s into %s' % (
            self.proposal.source_branch.display_name,
            self.proposal.target_branch.display_name)
        self.proposal.createComment(subject=subject, content=comment)
        self.proposal.setStatus(status=u'Needs review')
        self.proposal.lp_save()


tarmac_hooks['tarmac_pre_commit'].hook(Command(), 'Command plugin')
