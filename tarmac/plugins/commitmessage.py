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

    def run(self, command, target, source, proposal):
        # pylint: disable-msg=W0613

        template = target.config.get('commit_message_template')
        if template is None:
            return
        template = template.replace('<', '%(').replace('>', ')s')

        proposal.commit_message = self.render(
            template, CommitMessageTemplateInfo(proposal))

    def render(self, template, info):
        """Render a template using the given information."""
        return template % info


class CommitMessageTemplateInfo(object):

    def __init__(self, proposal):
        self._proposal = proposal

    def __getitem__(self, name):
        """Return the value of the attribute with the given name.

        Never returns None; the empty string is substituted.
        """
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
    def author_nick(self):
        """The short name of the source branch author."""
        return self._proposal.source_branch.owner.name

    @property
    def commit_message(self):
        """The commit message set in the merge proposal."""
        return self._proposal.commit_message

    @property
    def reviewer(self):
        """The display name of the merge proposal reviewer.

        This is the person that marked the *whole* proposal as
        approved, not necessarily an individual voter.
        """
        return self._proposal.reviewer.display_name

    def _get_approvers(self):
        for vote in self._proposal.votes:
            comment = vote.comment
            if comment is not None and comment.vote == 'Approve':
                yield vote.reviewer

    @property
    def approved_by(self):
        """Display name of reviewers who approved the review."""
        return ", ".join(
            reviewer.display_name for reviewer in self._get_approvers())

    @property
    def approved_by_nicks(self):
        """Short names of reviewers who approved the review."""
        return ",".join(
            reviewer.name for reviewer in self._get_approvers())

    @property
    def bugs_fixed(self):
        return ",".join(
            str(bug.id) for bug in self._proposal.source_branch.linked_bugs)

    @property
    def review_url(self):
        return self._proposal.web_link


tarmac_hooks['tarmac_pre_commit'].hook(
    CommitMessageTemplate(),
    'Commit messsage template editor.')
