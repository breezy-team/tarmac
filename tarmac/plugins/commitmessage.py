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

        if command.config.commit_message_template:
            self.template = command.config.commit_message_template
            self.template = self.template.replace('<', '%(').replace(
                '>', ')s')
        else:
            self.template = '%(commit_message)s'

        source.lp_branch.commit_message = self.render(
            self.template, CommitMessageTemplateInfo(proposal))

    def render(self, template, info):
        return template % info


class CommitMessageTemplateInfo(object):

    def __init__(self, proposal):
        self._proposal = proposal

    def __getitem__(self, name):
        if name.startswith('_'):
            value = None
        else:
            value = getattr(self, name, None)
        return ("" if value is None else value)

    @property
    def author(self):
        """The display name of the source branch author."""
        return self._proposal.source_branch.owner.display_name

    @property
    def commit_message(self):
        """The commit message set in the merge proposal."""
        return self._proposal.commit_message

    @property
    def reviewer(self):
        """The display name of the merge proposal reviewer."""
        return self._proposal.reviewer.display_name


tarmac_hooks['tarmac_pre_commit'].hook(CommitMessageTemplate(),
    'Commit messsage template editor.')
