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
import re

from lazr.restfulclient.errors import Unauthorized
from tarmac.exceptions import TarmacMergeError
from tarmac.hooks import tarmac_hooks
from tarmac.plugins import TarmacPlugin


class InvalidContributor(TarmacMergeError):
    """Error for when a contributor does not meet validation requirements."""


class InvalidPersonOrTeam(TarmacMergeError):
    """Error for when a required team could not be found."""


class AllowedContributors(TarmacPlugin):
    """Tarmac plug-in for checking whether a contributor is allowed to.

    This plug-in checks for the allowed_contributors setting on the target
    branch, and if found, will cause the branch merge to fail, if the authors
    of the branch, are not in the list, or members of teams in the list.
    """

    def run(self, command, target, source, proposal):
        """Check the allowed contributors list."""
        allowed_contributors = target.config.get('allowed_contributors')
        if allowed_contributors is None:
            return

        self.allowed_contributors = allowed_contributors.split(',')

        self.logger.debug(
            'Checking that authors of %s are allowed to '
            'contribute to %s',
            proposal.source_branch.display_name,
            proposal.target_branch.display_name)

        launchpad = command.launchpad

        invalid_contributors = []
        for name in source.authors:
            email = re.sub(r'>$', '', re.sub(r'^.*\<', '', name))
            author = launchpad.people.getByEmail(email=email)
            if author is None:
                invalid_contributors.append(email)
                continue

            if author.name in self.allowed_contributors:
                continue
            else:
                in_team = False
                for team in self.allowed_contributors:
                    try:
                        lp_team = launchpad.people[team]
                        if lp_team.is_team:
                            in_team = self.is_in_team(author, lp_team)
                            if in_team:
                                break
                    except Unauthorized:
                        raise InvalidPersonOrTeam(
                            'Received Unauthorized error while trying to '
                            'list members of team: %s' % team)
                    except KeyError:
                        message = ('Could not find person or team "%s" on '
                                   'Launchpad.' % team)
                        comment = (
                            'Merging into %(target) requires that '
                            'contributing authors be a member of an '
                            'acceptable team, or a specified person. '
                            'However, the person or team "%(team)s" '
                            'was not found on Launchpad.' % {
                                'target': proposal.target_branch.display_name,
                                'team': team})
                        raise InvalidPersonOrTeam(message, comment)

                if not in_team and name not in invalid_contributors:
                    invalid_contributors.append(name)

        if len(invalid_contributors) > 0:
            message = 'Some contributors are not acceptable.'
            comment = (
                'There was a problem validating some authors of the '
                'branch. Authors must be either one of the listed '
                'Launchpad users, or a member of one of the listed '
                'teams on Launchpad.\n\n'
                'Persons or Teams:\n\n    %(teams)s\n\n'
                'Unaccepted Authors:\n\n    %(authors)s' % {
                    'teams': '\n    '.join(sorted(self.allowed_contributors)),
                    'authors': '\n    '.join(sorted(invalid_contributors))})
            raise InvalidContributor(message, comment)

    def is_in_team(self, person, team):
        """Check that a person is a member of team, or one of its subteams."""
        for subteam in team.members:
            if str(subteam) == str(person):
                return True
            if subteam.is_team and self.is_in_team(person, subteam):
                return True
        return False


tarmac_hooks['tarmac_pre_commit'].hook(
    AllowedContributors(), 'Allowed contributors check plug-in')
