# This file is part of Tarmac.
#
# Copyright 2010 Canonical, Ltd.
#
# Tarmac is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# Tarmac is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tarmac.  If not, see <http://www.gnu.org/licenses/>.
"""Tarmac plug-in for checking for a list of allowable contributors."""
from tarmac.exceptions import TarmacMergeError
from tarmac.hooks import tarmac_hooks
from tarmac.plugins import TarmacPlugin


class InvalidContributor(TarmacMergeError):
    """Error for when a contributor does not meet validation requirements."""


class AllowedContributors(TarmacPlugin):
    """Tarmac plug-in for checking whether a contributor is allowed to.

    This plug-in checks for the allowed_contributors setting on the target
    branch, and if found, will cause the branch merge to fail, if the authors
    of the branch, are not in the list, or members of teams in the list.
    """

    def run(self, command, target, source, proposal):
        """Check the allowed contributors list."""
        try:
            self.allowed_contributors = target.config.allowed_contributors
            self.allowed_contributors = self.allowed_contributors.split(',')
        except AttributeError:
            return

        self.logger.debug('Checking that authors of %(source)s are allowed to '
                          'contribute to %(target)s' % {
                'source': proposal.source_branch.display_name,
                'target': proposal.target_branch.display_name})

        invalid_contributors = []
        for author in source.authors:
            if author in self.allowed_contributors:
                continue
            else:
                in_team = False
                for team in self.allowed_contributors:
                    launchpad = command.launchpad
                    lp_members = launchpad.people[team].getMembersByStatus(
                        status=[u'Approved', u'Administrator'])
                    members = [x.name for x in lp_members]
                    if author in members:
                        in_team = True
                        break
                if not in_team and author not in invalid_contributors:
                    invalid_contributors.append(author)
        if len(invalid_contributors) > 0:
            message = u'Some contributors are not acceptable.'
            comment = (u'There was a problem validating some authors of the '
                       u'branch. Authors must be either one of the listed '
                       u'Launchpad users, or a member of one of the listed '
                       u'teams on Launchpad.\n\n'
                       u'Persons or Teams:\n\n    %(teams)s\n\n'
                       u'Unaccepted Authors:\n\n    %(authors)s' % {
                    'teams': '\n    '.join(sorted(self.allowed_contributors)),
                    'authors': '\n    '.join(sorted(invalid_contributors))})
            raise InvalidContributor(message, comment)


tarmac_hooks['tarmac_pre_commit'].hook(
    AllowedContributors(), 'Allowed contributors check plug-in')
