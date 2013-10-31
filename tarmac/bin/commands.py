'''Command handling for Tarmac.'''
import httplib2
import logging
import os
import re

from bzrlib.commands import Command
from bzrlib.errors import PointlessMerge, LockContention
from bzrlib.help import help_commands
from launchpadlib.launchpad import Launchpad
from launchpadlib.uris import (LPNET_SERVICE_ROOT,
    STAGING_SERVICE_ROOT)

from tarmac.bin import options
from tarmac.branch import Branch
from tarmac.hooks import tarmac_hooks
from tarmac.log import set_up_debug_logging, set_up_logging
from tarmac.exceptions import (TarmacMergeError, TarmacCommandError,
                               UnapprovedChanges)
from tarmac.plugin import load_plugins
from tarmac.utility import get_review_url


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
            u'Tarmac', service_root=SERVICE_ROOT,
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
        options.one_option]

    def _do_merges(self, branch_url):

        lp_branch = self.launchpad.branches.getByUrl(url=branch_url)
        if lp_branch is None:
            self.logger.info('Not a valid branch: {0}'.format(branch_url))
            return

        proposals = self._get_mergable_proposals_for_branch(lp_branch)

        if not proposals:
            self.logger.info(
                'No approved proposals found for %(branch_url)s' % {
                    'branch_url': branch_url})
            return

        target = Branch.create(lp_branch, self.config, create_tree=True)

        self.logger.debug('Firing tarmac_pre_merge hook')
        tarmac_hooks.fire('tarmac_pre_merge',
                          self, target)

        success_count = 0
        try:
            for proposal in proposals:
                target.cleanup()
                self.logger.debug(
                    u'Preparing to merge %(source_branch)s' % {
                        'source_branch': proposal.source_branch.web_link})
                try:
                    prerequisite = proposal.prerequisite_branch
                    if prerequisite:
                        merges = [x for x in  prerequisite.landing_targets
                                  if x.target_branch == target.lp_branch and
                                  x.queue_status != u'Superseded']
                        if len(merges) == 0:
                            raise TarmacMergeError(
                                u'No proposals of prerequisite branch.',
                                u'No proposals found for merge of %s '
                                u'into %s.' % (
                                    prerequisite.web_link,
                                    target.lp_branch.web_link))
                        elif len(merges) > 1:
                            raise TarmacMergeError(
                                u'Too many proposals of prerequisite.',
                                u'More than one proposal found for merge '
                                u'of %s into %s, which is not Superseded.' % (
                                    prerequisite.web_link,
                                    target.lp_branch.web_link))
                        elif len(merges) == 1:
                            if merges[0].queue_status != u'Merged':
                                raise TarmacMergeError(
                                    u'Prerequisite not yet merged.',
                                    u'The prerequisite %s has not yet been '
                                    u'merged into %s.' % (
                                        prerequisite.web_link,
                                        target.lp_branch.web_link))

                    if not proposal.reviewed_revid:
                        raise TarmacMergeError(
                            u'No approved revision specified.')


                    source = Branch.create(
                        proposal.source_branch, self.config, target=target)

                    approved = source.bzr_branch.revision_id_to_revno(
                        str(proposal.reviewed_revid))
                    tip = source.bzr_branch.revno()

                    if tip > approved:
                        message = u'Unapproved changes made after approval'
                        lp_comment = (
                            u'There are additional revisions which have not '
                            u'been approved in review. Please seek review and '
                            u'approval of these new revisions.')
                        raise UnapprovedChanges(message, lp_comment)

                    self.logger.debug(
                        'Merging %(source)s at revision %(revision)s' % {
                            'source': proposal.source_branch.web_link,
                            'revision': proposal.reviewed_revid})

                    target.merge(source, str(proposal.reviewed_revid))

                    self.logger.debug('Firing tarmac_pre_commit hook')
                    tarmac_hooks.fire('tarmac_pre_commit',
                                      self, target, source, proposal)

                except TarmacMergeError, failure:
                    self.logger.warn(
                        u'Merging %(source)s into %(target)s failed: %(msg)s' %
                        {'source': proposal.source_branch.web_link,
                         'target': proposal.target_branch.web_link,
                         'msg': str(failure)})

                    subject = u'Re: [Merge] %(source)s into %(target)s' % {
                        "source": proposal.source_branch.display_name,
                        "target": proposal.target_branch.display_name}

                    if failure.comment:
                        comment = failure.comment
                    else:
                        comment = str(failure)

                    proposal.createComment(subject=subject, content=comment)
                    try:
                        proposal.setStatus(
                            status=self.config.rejected_branch_status)
                    except AttributeError:
                        proposal.setStatus(status=u'Needs review')
                    proposal.lp_save()

                    # If we've been asked to only merge one branch, then exit.
                    if self.config.one:
                        return True

                    continue
                except TarmacMergeSkipError:
                    self.logger.warn(
                        'SKipping merge of %(source)s into %(target)s.' % {
                            'source': proposal.source_branch.web_link,
                            'target': proposal.target_branch.web_link})
                    target.cleanup()
                    continue
                except PointlessMerge:
                    self.logger.warn(
                        'Merging %(source)s into %(target)s would be '
                        'pointless.' % {
                            'source': proposal.source_branch.web_link,
                            'target': proposal.target_branch.web_link})
                    continue

                merge_url = get_review_url(proposal)
                revprops = {'merge_url': merge_url}

                commit_message = proposal.commit_message
                if commit_message is None and self.config.imply_commit_message:
                    commit_message = proposal.description
                target.commit(commit_message,
                             revprops=revprops,
                             authors=source.authors,
                             reviews=self._get_reviews(proposal))

                self.logger.debug('Firing tarmac_post_commit hook')
                tarmac_hooks.fire('tarmac_post_commit',
                                  self, target, source, proposal)
                success_count += 1
                target.cleanup()
                if self.config.one:
                    return True

        # This except is here because we need the else and can't have it
        # without an except as well.
        except:
            raise
        else:
            self.logger.debug('Firing tarmac_post_merge hook')
            tarmac_hooks.fire('tarmac_post_merge',
                              self, target, success_count=success_count)
        finally:
            target.cleanup()

    def _get_mergable_proposals_for_branch(self, lp_branch):
        """Return a list of the mergable proposals for the given branch."""
        proposals = []
        for entry in lp_branch.landing_candidates:
            self.logger.debug("Considering merge proposal: {0}".format(entry.web_link))

            if entry.queue_status != u'Approved':
                self.logger.debug(
                    "  Skipping proposal: status is {0}, not "
                    "'Approved'".format(entry.queue_status))
                continue

            if (not self.config.imply_commit_message and
                not entry.commit_message):
                self.logger.debug(
                    "  Skipping proposal: proposal has no commit message")
                continue

            proposals.append(entry)
        return proposals

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

    def run(self, branch_url=None, launchpad=None, **kwargs):
        for key, value in kwargs.iteritems():
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

        if branch_url:
            self.logger.debug('%(branch_url)s specified as branch_url' % {
                'branch_url': branch_url})
            if not branch_url.startswith('lp:'):
                raise TarmacCommandError('Branch urls must start with lp:')
            self._do_merges(branch_url)

        else:
            for branch in self.config.branches:
                self.logger.debug(
                    'Merging approved branches against %(branch)s' % {
                        'branch': branch})
                try:
                    merged = self._do_merges(branch)

                    # If we've been asked to only merge one branch, then exit.
                    if merged and self.config.one:
                        break
                except LockContention:
                    continue
                except Exception, error:
                    self.logger.error(
                        'An error occurred trying to merge %s: %s',
                        branch, error)
                    raise
