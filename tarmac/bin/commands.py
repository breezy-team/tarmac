# Copyright 2009-2012 Paul Hummer
# Copyright 2009-2014 Canonical Ltd.
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
'''Command handling for Tarmac.'''
import httplib2
import logging
import os
import re

from breezy.commands import Command
from breezy.errors import LockContention
from breezy.help import help_commands
from breezy.workingtree import PointlessMerge
from launchpadlib.launchpad import Launchpad
from launchpadlib.uris import (
    LPNET_SERVICE_ROOT,
    STAGING_SERVICE_ROOT,
)

from tarmac.bin import options
from tarmac.branch import Branch
from tarmac.hooks import tarmac_hooks
from tarmac.log import set_up_debug_logging, set_up_logging
from tarmac.exceptions import (
    TarmacCommandError,
    TarmacMergeError,
    TarmacMergeSkipError,
    UnapprovedChanges,
)
from tarmac.plugin import load_plugins


def sort_landing_candidates(proposals):
    unique_names = {
        p.source_branch.unique_name: (
            p.prerequisite_branch.unique_name
            if p.prerequisite_branch else None)
        for p in proposals}

    def key(p):
        """Helper to sort proposals based on a prerequisite branch"""
        c = 0
        b = p.source_branch.unique_name
        while unique_names.get(b) in unique_names:
            c += 1
            b = unique_names.get(b)
        return c

    return sorted(proposals, key=key)


class TarmacCommand(Command):
    '''A command class.'''

    NAME = None

    def __init__(self, registry):
        Command.__init__(self)

        self.config = registry.config
        self.registry = registry

        set_up_logging(self.config)
        self.logger = logging.getLogger('tarmac')

        for option in self.takes_options:
            name = re.sub(r'-', '_', option.name)
            self.config.set('Tarmac', name, False)

    def _usage(self):
        """Custom _usage for referencing 'tarmac' instead of 'bzr'."""
        s = 'tarmac ' + self.name() + ' '
        for aname in self.takes_args:
            aname = aname.upper()
            if aname[-1] in ['$', '+']:
                aname = aname[:-1] + '...'
            elif aname[-1] == '?':
                aname = '[' + aname[:-1] + ']'
            elif aname[-1] == '*':
                aname = '[' + aname[:-1] + '...]'
            s += aname + ' '
        s = s[:-1]
        return s

    def run(self):
        '''Actually run the command.'''

    def get_launchpad_object(self, filename=None, staging=False):
        '''Return a Launchpad object for making API requests.'''
        # XXX: rockstar - 2009 Dec 13 - Ideally, we should be using
        # Launchpad.login_with, but currently, it doesn't support the option of
        # putting the credentials file somewhere other than where the cache
        # goes, and that's kinda nasty (and a security issue according to
        # Kees).
        if not filename:
            filename = self.config.CREDENTIALS

        if staging:
            SERVICE_ROOT = STAGING_SERVICE_ROOT
        else:
            SERVICE_ROOT = LPNET_SERVICE_ROOT

        self.logger.debug(
            "Connecting to the Launchpad API at {0}".format(SERVICE_ROOT))

        self.logger.debug("  Loading credentials from {0}".format(filename))
        if not os.path.exists(filename):
            self.logger.debug("  No existing API credentials were found")
            self.logger.debug("  Fetching new credentials from {0}".format(
                SERVICE_ROOT))

        launchpad = Launchpad.login_with(
            'Tarmac', service_root=SERVICE_ROOT,
            credentials_file=filename,
            launchpadlib_dir=self.config.CACHE_HOME)

        self.logger.debug("Connected")
        return launchpad


class cmd_authenticate(TarmacCommand):
    '''Create an OAuth token to be used by Tarmac.

    In order to use Tarmac at all, one must authenticate with Launchpad.  This
    command facilitates the process of getting an OAuth token from Launchpad.
    '''

    aliases = ['auth']
    takes_args = ['filename?']
    takes_options = [options.staging_option]

    def run(self, filename=None, staging=False):
        if os.path.exists(self.config.CREDENTIALS):
            self.logger.error('You have already been authenticated.')
        else:
            self.get_launchpad_object(filename=filename,
                                      staging=staging)


class cmd_help(TarmacCommand):
    '''Get help for Tarmac commands.'''

    aliases = ['fubar']
    takes_args = ['command?']

    def run(self, command=None):
        if command is None:
            self.outf.write('Usage:     tarmac <command> <options>\n\n')
            self.outf.write('Available commands:\n')
            self.help_commands()
        else:
            cmd = self.registry._get_command(None, command)
            if cmd is None:
                self.outf.write('Unknown command "%(command)s"\n' % {
                    'command': command})
                return
            text = cmd.get_help_text()
            if text:
                self.outf.write(text)

    def help_commands(self):
        help_commands(self.outf)


class cmd_merge(TarmacCommand):
    '''Automatically merge approved merge proposal branches.'''

    aliases = ['land']
    takes_args = ['branch_url?']
    takes_options = [
        options.http_debug_option,
        options.debug_option,
        options.imply_commit_message_option,
        options.one_option,
        options.list_approved_option,
        options.proposal_option,
        options.dry_run_option,
    ]

    def _handle_merge_error(self, proposal, failure, dry_run):
        """Handle TarmacMergeError cases from _do_merges."""
        self.logger.warning(
            'Merging %(source)s into %(target)s failed: %(msg)s' %
            {'source': proposal.source_branch.web_link,
             'target': proposal.target_branch.web_link,
             'msg': str(failure)})

        subject = 'Re: [Merge] %(source)s into %(target)s' % {
            "source": proposal.source_branch.display_name,
            "target": proposal.target_branch.display_name}

        if failure.comment:
            comment = failure.comment
        else:
            comment = str(failure)

        if not dry_run:
            proposal.createComment(subject=subject, content=comment)
            if self.config.rejected_branch_status is not None:
                proposal.setStatus(status=self.config.rejected_branch_status)
            else:
                proposal.setStatus(status='Needs review')
            proposal.lp_save()

    def _do_merges(self, branch_url, source_mp=None, dry_run=False):
        """Merge the approved proposals for %branch_url."""
        lp_branch = self.launchpad.branches.getByUrl(url=branch_url)
        if lp_branch is None:
            self.logger.info('Not a valid branch: {0}'.format(branch_url))
            return

        if source_mp is not None:
            proposals = [source_mp]
        else:
            proposals = self._get_mergable_proposals_for_branch(lp_branch)

        if not proposals:
            self.logger.info(
                'No approved proposals found for %(branch_url)s' % {
                    'branch_url': branch_url})
            return

        if self.config.list_approved:
            for proposal in proposals:
                print((proposal.web_link))
            return

        try:
            target = Branch.create(
                lp_branch, config=self.config, create_tree=True,
                launchpad=self.launchpad)
        except TarmacMergeError as failure:
            self._handle_merge_error(proposals[0], failure, dry_run)
            return

        self.logger.debug('Firing tarmac_pre_merge hook')
        tarmac_hooks.fire('tarmac_pre_merge',
                          self, target)

        success_count = 0
        try:
            for proposal in proposals:
                target.cleanup()
                self.logger.debug(
                    'Preparing to merge %(source_branch)s' % {
                        'source_branch': proposal.source_branch.web_link})
                try:
                    prerequisite = proposal.prerequisite_branch
                    if prerequisite:
                        merges = self._get_prerequisite_proposals(proposal)
                        if len(merges) == 0:
                            raise TarmacMergeError(
                                'No proposals of prerequisite branch.',
                                'No proposals found for merge of %s '
                                'into %s.' % (
                                    prerequisite.web_link,
                                    target.lp_branch.web_link))
                        elif len(merges) > 1:
                            raise TarmacMergeError(
                                'Too many proposals of prerequisite.',
                                'More than one proposal found for merge '
                                'of %s into %s, which is not Superseded.' % (
                                    prerequisite.web_link,
                                    target.lp_branch.web_link))

                    if not proposal.reviewed_revid:
                        raise TarmacMergeError(
                            'No approved revision specified.')

                    source = Branch.create(
                        proposal.source_branch, config=self.config,
                        target=target, launchpad=self.launchpad)

                    approved = source.bzr_branch.revision_id_to_revno(
                        proposal.reviewed_revid.encode('utf-8'))
                    tip = source.bzr_branch.revno()

                    if tip > approved:
                        message = 'Unapproved changes made after approval'
                        lp_comment = (
                            'There are additional revisions which have not '
                            'been approved in review. Please seek review and '
                            'approval of these new revisions.')
                        raise UnapprovedChanges(message, lp_comment)

                    self.logger.debug(
                        'Merging %(source)s at revision %(revision)s' % {
                            'source': proposal.source_branch.web_link,
                            'revision': proposal.reviewed_revid})

                    target.merge(
                        source, proposal.reviewed_revid.encode('utf-8'))

                    self.logger.debug('Firing tarmac_pre_commit hook')
                    tarmac_hooks.fire('tarmac_pre_commit',
                                      self, target, source, proposal)

                except TarmacMergeError as failure:
                    self._handle_merge_error(proposal, failure, dry_run)

                    # If we've been asked to only merge one branch, then exit.
                    if self.config.one:
                        return True

                    continue
                except TarmacMergeSkipError as failure:
                    self.logger.warning(
                        'Skipping merge of %(source)s into %(target)s:'
                        ' %(msg)s' % {
                            'source': proposal.source_branch.web_link,
                            'target': proposal.target_branch.web_link,
                            'msg': str(failure),
                        })
                    target.cleanup()
                    continue
                except PointlessMerge:
                    self.logger.warning(
                        'Merging %(source)s into %(target)s would be '
                        'pointless.' % {
                            'source': proposal.source_branch.web_link,
                            'target': proposal.target_branch.web_link})
                    continue

                revprops = {'merge_url': proposal.web_link}

                commit_message = proposal.commit_message
                if commit_message is None and self.config.imply_commit_message:
                    commit_message = proposal.description
                target.commit(commit_message,
                              revprops=revprops,
                              authors=source.authors,
                              dry_run=dry_run,
                              reviews=self._get_reviews(proposal))
                target.merge_tags(source)

                self.logger.debug('Firing tarmac_post_commit hook')
                tarmac_hooks.fire('tarmac_post_commit',
                                  self, target, source, proposal)
                success_count += 1
                target.cleanup()
                if self.config.one:
                    return True

        # This except is here because we need the else and can't have it
        # without an except as well.
        except BaseException:
            raise
        else:
            self.logger.debug('Firing tarmac_post_merge hook')
            tarmac_hooks.fire('tarmac_post_merge',
                              self, target, success_count=success_count)
        finally:
            target.cleanup()

    def _get_mergable_proposals_for_branch(self, lp_branch):
        """
        Return a list of the mergable proposals for the given branch.  The
        list returned will be in the order that they should be processed.
        """
        proposals = []
        sorted_proposals = sort_landing_candidates(
            lp_branch.landing_candidates)
        for entry in sorted_proposals:
            self.logger.debug(
                "Considering merge proposal: {0}".format(entry.web_link))
            prereqs = self._get_prerequisite_proposals(entry)

            if entry.queue_status != 'Approved':
                self.logger.debug(
                    "  Skipping proposal: status is {0}, not "
                    "'Approved'".format(entry.queue_status))
                continue

            if (not self.config.imply_commit_message and
                    not entry.commit_message):
                self.logger.debug(
                    "  Skipping proposal: proposal has no commit message")
                continue

            if len(prereqs) == 1 and prereqs[0].queue_status != 'Merged':
                # N.B.: The case of a MP with more than one prereq MP open
                #       will be caught as a merge error.
                self.logger.debug(
                    "  Skipping proposal: prerequisite not yet merged")
                continue

            proposals.append(entry)
        return proposals

    def _get_prerequisite_proposals(self, proposal):
        """
        Given a proposal, return all prerequisite
        proposals that are not in the superseded state.  There ideally
        should be one and only one here (or zero), but sometimes there
        are not, depending on developer habits
        """
        prerequisite = proposal.prerequisite_branch
        target_branch = proposal.target_branch
        if not prerequisite or not prerequisite.landing_targets:
            return []
        return [
            x for x in prerequisite.landing_targets
            if x.target_branch.unique_name == target_branch.unique_name
            and x.queue_status != 'Superseded']

    def _get_reviews(self, proposal):
        """Get the set of reviews from the proposal."""
        reviews = []
        for vote in proposal.votes:
            if not vote.comment:
                continue
            else:
                reviews.append('%s;%s' % (vote.reviewer.display_name,
                                          vote.comment.vote))

        if len(reviews) == 0:
            return None

        return reviews

    def _get_proposal_from_mp_url(self, mp_url):
        """Return a branch_merge_proposal object from its web URL."""
        urlp = re.compile(r'http[s]?://code.launchpad\.net/')
        api_url = urlp.sub('https://api.launchpad.net/1.0/', mp_url)
        return self.launchpad.load(api_url)

    def run(self, branch_url=None, launchpad=None, dry_run=False, **kwargs):
        for key, value in list(kwargs.items()):
            self.config.set('Tarmac', key, value)

        if self.config.debug:
            set_up_debug_logging()
            self.logger.debug('Debug logging enabled')
        if self.config.http_debug:
            httplib2.debuglevel = 1
            self.logger.debug('HTTP debugging enabled.')
        self.logger.debug('Loading plugins')
        load_plugins()
        self.logger.debug('Plugins loaded')

        self.launchpad = launchpad
        if self.launchpad is None:
            self.logger.debug('Loading launchpad object')
            self.launchpad = self.get_launchpad_object()
            self.logger.debug('launchpad object loaded')

        proposal = None
        if self.config.proposal:
            proposal = self._get_proposal_from_mp_url(self.config.proposal)
            # Always override branch_url with the correct one.
            branch_url = proposal.target_branch.bzr_identity

        if branch_url:
            self.logger.debug('%(branch_url)s specified as branch_url' % {
                'branch_url': branch_url})
            if not branch_url.startswith('lp:'):
                raise TarmacCommandError('Branch urls must start with lp:')
            self._do_merges(branch_url, source_mp=proposal, dry_run=dry_run)

        else:
            for branch in self.config.branches:
                self.logger.debug(
                    'Merging approved branches against %(branch)s' % {
                        'branch': branch})
                try:
                    merged = self._do_merges(branch, dry_run=dry_run)

                    # If we've been asked to only merge one branch, then exit.
                    if merged and self.config.one:
                        break
                except LockContention:
                    continue
                except Exception as error:
                    self.logger.error(
                        'An error occurred trying to merge %s: %s',
                        branch, error)
                    raise
