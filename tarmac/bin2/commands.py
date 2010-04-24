'''Command handling for Tarmac.'''
import logging
import os
import re

from bzrlib.commands import Command
from bzrlib.errors import PointlessMerge
from launchpadlib.launchpad import (Credentials, Launchpad, EDGE_SERVICE_ROOT,
    STAGING_SERVICE_ROOT)

from tarmac.bin2 import options
from tarmac.branch import Branch2
from tarmac.config import TarmacConfig2
from tarmac.hooks import tarmac_hooks
from tarmac.exceptions import BranchHasConflicts, TarmacCommandError


class TarmacCommand(Command):
    '''A command class.'''

    NAME = None

    def _usage(self):
        return ''

    def __init__(self):
        Command.__init__(self)
        self.config = TarmacConfig2()

        # Set up logging.
        self.logger = logging.getLogger('tarmac')
        self.logger.addHandler(
            logging.FileHandler(filename=self.config.log_file))

        # If debugging. uncomment these lines.
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(stderr_handler)


    def run(self):
        '''Actually run the command.'''
        raise NotImplementedError

    # XXX: rockstar - DON'T RELEASE with staging as the default!!!!!!
    def get_launchpad_object(self, filename=None, staging=True):
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
            try:
                credentials.load(open(filename))
            except Exception, e:
                raise Exception('Something is wrong at %s' % (filename))
            launchpad = Launchpad(
                credentials, SERVICE_ROOT, self.config.CACHE_HOME)
        return launchpad


class cmd_authenticate(TarmacCommand):

    aliases = ['auth']
    takes_args = ['filename?']
    takes_options = [
        options.staging_option,]

    def run(self, filename=None, staging=False):
        # TODO: rockstar - DON'T RELEASE with staging as the default!!!!!!
        staging = True
        if os.path.exists(self.config.CREDENTIALS):
            self.logger.error('You have already been authenticated.')
        else:
            launchpad = self.get_launchpad_object(filename=filename,
                staging=staging)


class cmd_help(TarmacCommand):

    aliases = ['fubar']
    takes_args = []

    def run(self):
        print 'You need help.'


class cmd_merge(TarmacCommand):

    aliases = ['land',]
    takes_args = ['branch_url?']
    takes_options = []

    def _do_merges(self, branch_url):

        lp_branch = self.launchpad.branches.getByUrl(url=branch_url)

        candidates = [entry for entry in lp_branch.landing_candidates
                        if entry.queue_status == u'Approved' and
                        entry.commit_message]
        if not candidates:
            self.logger.info(
                'No landing candidates found for %{branch_url}s' % {
                    'branch_url': branch_url,})
            return

        target = Branch2.create(lp_branch, self.config, create_tree=True)
        for candidate in candidates:

            source = Branch2.create(
                candidate.source_branch, self.config)

            try:
                target.merge(source)

            except BranchHasConflicts:
                subject = (
                    u"Conflicts merging %(source)s into %(target)s" %
                    {"source": candidate.source_branch.display_name,
                     "target": candidate.target_branch.display_name})
                comment = (
                    u"Attempt to merge %(source)s into %(target)s failed due "
                    u"to merge conflicts:\n\n%(output)s" % {
                        "source": candidate.source_branch.display_name,
                        "target": candidate.target_branch.display_name,
                        "output": target.get_conflicts()})
                candidate.createComment(subject=subject, content=comment)
                candidate.setStatus(status=u"Needs review")
                candidate.lp_save()
                target.cleanup()
                continue

            except PointlessMerge:
                target.cleanup()
                continue

            urlp = re.compile('http[s]?://api\.(.*)launchpad\.net/beta/')
            merge_url = urlp.sub('http://launchpad.net/', candidate.self_link)
            revprops = { 'merge_url' : merge_url }
            try:
                self.logger.debug('Firing tarmac_pre_commit hook')
                tarmac_hooks['tarmac_pre_commit'].fire(
                    self, target, source, candidate)
                if self.dry_run:
                    target.cleanup()
                else:
                    target.commit(candidate.commit_message,
                                 revprops=revprops,
                                 authors=source.authors,
                                 reviewers=self._get_reviewers(candidate))

                self.logger.debug('Firing tarmac_post_commit hook')
                tarmac_hooks['tarmac_post_commit'].fire(
                    self, target, source, candidate)

            except Exception, e:
                self.logger.error("Oops! Tarmac hooks failed:\n%s" % e)

            target.cleanup()

    def run(self, branch_url=None):

        self.launchpad = self.get_launchpad_object()
        if branch_url:
            if not branch_url.startswith('lp:'):
                raise TarmacCommandError('Branch urls must start with lp:')
            self._do_merges(branch_url)

        else:
            for branch in self.config.branches:
                self.logger.info(
                    'Merging %(branch)s' % {'branch': branch})
                self._do_merges(branch)
