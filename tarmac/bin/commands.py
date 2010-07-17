'''Command handling for Tarmac.'''
import logging
import os
import re
import sys

from bzrlib.commands import Command
from bzrlib.errors import PointlessMerge
from bzrlib.help import help_commands
from launchpadlib.launchpad import (Credentials, Launchpad, EDGE_SERVICE_ROOT,
    STAGING_SERVICE_ROOT)

from ConfigParser import NoSectionError

from tarmac.bin import options
from tarmac.branch import Branch
from tarmac.config import TarmacConfig
from tarmac.hooks import tarmac_hooks
from tarmac.exceptions import BranchHasConflicts, TarmacCommandError
from tarmac.plugin import load_plugins


class TarmacCommand(Command):
    '''A command class.'''

    NAME = None

    def __init__(self, registry):
        Command.__init__(self)

        self.config = TarmacConfig()
        self.registry = registry

        # Set up logging.
        self.logger = logging.getLogger('tarmac')
        self.logger.setLevel(logging.WARNING)

        try:
            log_file = self.config.get('Tarmac', 'log_file')
        except NoSectionError:
            pass
        else:
            file_handler = logging.FileHandler(filename=log_file)
            file_handler.setLevel(logging.WARNING)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s %(levelname)-8s %(message)s',
                                  '%Y-%m-%d %H:%M:%S'))
            self.logger.addHandler(file_handler)

    def run(self):
        '''Actually run the command.'''
        raise NotImplementedError

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

    def set_debugging(self):
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(stderr_handler)



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
        options.debug_option]

    def _do_merges(self, branch_url):

        lp_branch = self.launchpad.branches.getByUrl(url=branch_url)

        proposals = [entry for entry in lp_branch.landing_candidates
                        if entry.queue_status == u'Approved' and
                        entry.commit_message]
        if not proposals:
            self.logger.info(
                'No approved proposals found for %(branch_url)s' % {
                    'branch_url': branch_url,})
            return

        target = Branch.create(lp_branch, self.config, create_tree=True)
        for proposal in proposals:

            self.logger.info(
                u'Preparing to merge %(source_branch)s' % {
                    'source_branch': proposal.source_branch.bzr_identity})
            source = Branch.create(
                proposal.source_branch, self.config)

            try:
                target.merge(source)

            except BranchHasConflicts:
                subject = (
                    u"Conflicts merging %(source)s into %(target)s" %
                    {"source": proposal.source_branch.display_name,
                     "target": proposal.target_branch.display_name})
                comment = (
                    u"Attempt to merge %(source)s into %(target)s failed due "
                    u"to merge conflicts:\n\n%(output)s" % {
                        "source": proposal.source_branch.display_name,
                        "target": proposal.target_branch.display_name,
                        "output": target.conflicts})
                proposal.createComment(subject=subject, content=comment)
                proposal.setStatus(status=u"Needs review")
                proposal.lp_save()
                target.cleanup()
                continue

            except PointlessMerge:
                target.cleanup()
                continue

            urlp = re.compile('http[s]?://api\.(.*)launchpad\.net/beta/')
            merge_url = urlp.sub('http://launchpad.net/', proposal.self_link)
            revprops = { 'merge_url' : merge_url }
            self.logger.info('Firing tarmac_pre_commit hook')
            tarmac_hooks['tarmac_pre_commit'].fire(
                self, target, source, proposal)
            target.commit(proposal.commit_message,
                         revprops=revprops,
                         authors=source.authors,
                         reviewers=self._get_reviewers(proposal))

            self.logger.info('Firing tarmac_post_commit hook')
            tarmac_hooks['tarmac_post_commit'].fire(
                self, target, source, proposal)

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

    def run(self, branch_url=None, launchpad=None, debug=False):
        if debug:
            self.set_debugging()
        load_plugins()

        self.launchpad = launchpad
        if self.launchpad is None:
            self.launchpad = self.get_launchpad_object()

        if branch_url:
            if not branch_url.startswith('lp:'):
                raise TarmacCommandError('Branch urls must start with lp:')
            self._do_merges(branch_url)

        else:
            for branch in self.config.branches:
                self.logger.info(
                    'Merging approved branches against %(branch)s' % {
                        'branch': branch})
                self._do_merges(branch)
