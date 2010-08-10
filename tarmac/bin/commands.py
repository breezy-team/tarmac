'''Command handling for Tarmac.'''
import httplib2
import logging
import os
import re

from bzrlib.commands import Command
from bzrlib.errors import PointlessMerge, TipChangeRejected
from bzrlib.help import help_commands
from launchpadlib.launchpad import (Credentials, Launchpad, EDGE_SERVICE_ROOT,
    STAGING_SERVICE_ROOT)

from tarmac.bin import options
from tarmac.branch import Branch
from tarmac.config import TarmacConfig
from tarmac.hooks import tarmac_hooks
from tarmac.log import set_up_debug_logging, set_up_logging
from tarmac.exceptions import (BranchHasConflicts, TarmacCommandError,
                               UnapprovedChanges)
from tarmac.plugin import load_plugins


class TarmacCommand(Command):
    '''A command class.'''

    NAME = None

    def __init__(self, registry):
        Command.__init__(self)

        self.config = TarmacConfig()
        self.registry = registry

        set_up_logging()
        self.logger = logging.getLogger('tarmac')

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
            SERVICE_ROOT = EDGE_SERVICE_ROOT

        if not os.path.exists(filename):
            launchpad = Launchpad.get_token_and_login(
                'Tarmac', SERVICE_ROOT, self.config.CACHE_HOME)
            launchpad.credentials.save(file(filename, 'w'))
        else:
            credentials = Credentials()
            credentials.load(open(filename))
            launchpad = Launchpad(
                credentials, SERVICE_ROOT, self.config.CACHE_HOME)
        return launchpad


class cmd_authenticate(TarmacCommand):
    '''Create an OAuth token to be used by Tarmac.

    In order to use Tarmac at all, one must authenticate with Launchpad.  This
    command facilitates the process of getting an OAuth token from Launchpad.
    '''

    aliases = ['auth']
    takes_args = ['filename?',]
    takes_options = [
        options.staging_option,]

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
                self.outf.write('Unknown command "%{command}s"\n' % {
                    'command': command,})
                return
            text = cmd.get_help_text()
            if text:
                self.outf.write(text)

    def help_commands(self):
        help_commands(self.outf)


class cmd_merge(TarmacCommand):
    '''Automatically merge approved merge proposal branches.'''

    aliases = ['land',]
    takes_args = ['branch_url?']
    takes_options = [
        options.http_debug_option,
        options.debug_option,
        options.imply_commit_message_option]

    def _do_merges(self, branch_url, imply_commit_message):

        lp_branch = self.launchpad.branches.getByUrl(url=branch_url)

        proposals = [entry for entry in lp_branch.landing_candidates
                        if entry.queue_status == u'Approved' and
                        (imply_commit_message or entry.commit_message)]
        if not proposals:
            self.logger.info(
                'No approved proposals found for %(branch_url)s' % {
                    'branch_url': branch_url,})
            return

        target = Branch.create(lp_branch, self.config, create_tree=True)

        self.logger.debug('Firing tarmac_pre_merge hook')
        tarmac_hooks['tarmac_pre_merge'].fire(
            self, target)

        try:
            for proposal in proposals:

                self.logger.debug(
                    u'Preparing to merge %(source_branch)s' % {
                        'source_branch': proposal.source_branch.bzr_identity})
                source = Branch.create(
                    proposal.source_branch, self.config)

                try:
                    approved = proposal.reviewed_revid
                    tip = proposal.source_branch.revision_count
                    if tip > approved:
                        raise UnapprovedChanges(
                            'Unapproved changes to branch after approval.')

                    self.logger.debug(
                        'Merging %(source)s at revision %(revision)s' % {
                            'source': proposal.source_branch.display_name,
                            'revision': proposal.reviewed_revid,})

                    target.merge(
                        source,
                        str(proposal.reviewed_revid))

                    self.logger.debug('Firing tarmac_pre_commit hook')
                    tarmac_hooks['tarmac_pre_commit'].fire(
                        self, target, source, proposal)

                except Exception, failure:
                    subject = u'Re: [Merge] %(source)s into %(target)s' % {
                        "source": proposal.source_branch.display_name,
                        "target": proposal.target_branch.display_name,}
                    comment = None
                    if isinstance(failure, BranchHasConflicts):
                        self.logger.warn(
                            u'Conflicts merging %(source)s into %(target)s' % {
                                "source": proposal.source_branch.display_name,
                                "target": proposal.target_branch.display_name})
                        comment = (
                            u'Attempt to merge %(source)s into %(target)s '
                            u'failed due to merge conflicts:\n\n%(output)s' % {
                                "source": proposal.source_branch.display_name,
                                "target": proposal.target_branch.display_name,
                                "output": target.conflicts})
                    elif isinstance(failure, PointlessMerge):
                        self.logger.warn(
                            'Merging %(source)s into %(target)s would be '
                            'pointless.' % {
                                'source': proposal.source_branch.display_name,
                                'target': proposal.target_branch.display_name,})
                        comment = (
                            u'There is no resulting diff between %(source)s '
                            u'and %(target)s.' % {
                                "source": proposal.source_branch.display_name,
                                "target": proposal.target_branch.display_name,})
                    elif isinstance(failure, TipChangeRejected):
                        comment = failure.msg
                    elif isinstance(failure, UnapprovedChanges):
                        self.logger.warn(
                            u'Unapproved chagnes to %(source) were made '
                            u'after approval for merge into %(target).' % {
                                "source": proposal.source_branch.display_name,
                                "target": proposal.target_branch.display_name,})
                        comment = (
                            u'There are additional revisions which have not '
                            u'been approved in review. Please seek review and '
                            u'approval of these revisions as well.')
                    else:
                        raise failure

                    proposal.createComment(subject=subject, content=comment)
                    proposal.setStatus(status=u'Needs review')
                    proposal.lp_save()
                    self.logger.warn(
                        'Conflicts found while merging %(source)s into '
                        '%(target)s,' % {
                            'source': proposal.source_branch.display_name,
                            'target': proposal.target_branch.display_name,})
                    target.cleanup()
                    continue

                urlp = re.compile('http[s]?://api\.(.*)launchpad\.net/beta/')
                merge_url = urlp.sub(
                    'http://launchpad.net/', proposal.self_link)
                revprops = { 'merge_url' : merge_url }

                commit_message = proposal.commit_message
                if commit_message is None and imply_commit_message:
                    commit_message = proposal.description
                target.commit(commit_message,
                             revprops=revprops,
                             authors=source.authors,
                             reviewers=self._get_reviewers(proposal))

                self.logger.debug('Firing tarmac_post_commit hook')
                tarmac_hooks['tarmac_post_commit'].fire(
                    self, target, source, proposal)

                target.cleanup()

        # This except is here because we need the else and can't have it
        # without an except as well.
        except Exception, e:
            raise e
        else:
            self.logger.debug('Firing tarmac_post_merge hook')
            tarmac_hooks['tarmac_post_merge'].fire(
                self, target)
        finally:
            target.cleanup()

    def _get_reviewers(self, candidate):
        '''Get all reviewers who approved the review.'''
        reviewers = []
        for vote in candidate.votes:
            if not vote.comment:
                continue
            elif vote.comment and vote.comment.vote == u'Approve' and \
                    candidate.source_branch.isPersonTrustedReviewer(
                reviewer=vote.reviewer):
                    reviewers.append(vote.reviewer.display_name)

        if len(reviewers) == 0:
            return None

        return reviewers

    def run(self, branch_url=None, debug=False, http_debug=False,
            launchpad=None, imply_commit_message=False):
        if debug:
            set_up_debug_logging()
            self.logger.debug('Debug logging enabled')
        if http_debug:
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

        if branch_url:
            self.logger.debug(
                '%(branch_url)s specified as branch_url' % {
                    'branch_url': branch_url,})
            if not branch_url.startswith('lp:'):
                raise TarmacCommandError('Branch urls must start with lp:')
            self._do_merges(branch_url, imply_commit_message)

        else:
            for branch in self.config.branches:
                self.logger.debug(
                    'Merging approved branches against %(branch)s' % {
                        'branch': branch})
                self._do_merges(branch)
