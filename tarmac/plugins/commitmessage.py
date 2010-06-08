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

'''Tarmac plugin for enforcing a commit message format.'''
from tarmac.hooks import tarmac_hooks
from tarmac.plugins import TarmacPlugin


class CommitMessageTemplate(TarmacPlugin):
    '''Tarmac plugin for modifying the commit message to adhere to a template.

    This plugin checks for a commit_message_template specific to the project.
    If to finds one, it will locally change the commit message to use the
    template.
    '''

    def __call__(self, command, target, source, proposal):
    # pylint: disable-msg=W0613
        try:
            self.template = target.config.commit_message_template
            self.template = self.template.replace('<', '%(').replace(
                '>', ')s')
        except AttributeError:
            return

        proposal.commit_message = self.template % {
            'author': proposal.source_branch.owner.display_name,
            'commit_message': proposal.commit_message,
            'reviewer': proposal.reviewer.display_name}

tarmac_hooks['tarmac_pre_commit'].hook(CommitMessageTemplate(),
    'Commit messsage template editor.')
