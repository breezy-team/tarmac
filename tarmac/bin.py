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

'''Code used by Tarmac scripts.'''
import atexit
import logging
from optparse import OptionParser
import os
import sys

from bzrlib.errors import PointlessMerge
from bzrlib.plugin import load_plugins as load_bzr_plugins
from launchpadlib.errors import HTTPError

from tarmac.branch import Branch
from tarmac.config import TarmacConfig
from tarmac.hooks import tarmac_hooks
from tarmac.plugin import load_plugins
from tarmac.utils import get_launchpad_object

load_bzr_plugins()
load_plugins()


class TarmacScript:
    '''An abstract script for reusable parts of Tarmac.'''

    def __init__(self, test_mode=False):
        self.parser = self._create_option_parser()
        self.options, self.args = self.parser.parse_args()
        self.test_mode = test_mode

    def create_pid(self):
        '''Create a pidfile for the running process.'''
        assert not os.path.exists(self.configuration.PID_FILE)
        pidfile = open(self.configuration.PID_FILE, 'wb')
        pidfile.write(str(os.getpid()))
        pidfile.close()
        atexit.register(self.delete_pid)

    def delete_pid(self):
        '''Delete the pid file.

        This method is usually called when the atexit signal is emitted.
        '''
        assert os.path.exists(self.configuration.PID_FILE)
        os.remove(self.configuration.PID_FILE)

    def _create_option_parser(self):
        '''Create the option parser.'''
        raise NotImplementedError

    def main(self):
        '''Main part of each script.'''
        raise NotImplementedError


class TarmacAuthenticate(TarmacScript):
    '''Tarmac authentication script.

    This script is intended do nothing but get an OAuth token from Launchpad,
    and (optionally) output that token to a specified file.
    '''
    def __init__(self, test_mode=False):
        TarmacScript.__init__(self, test_mode)

        self.configuration = TarmacConfig()

        try:
            self.filename = self.args[0]
        except IndexError:
            self.filename = None

    def _create_option_parser(self):
        '''See `TarmacScript._create_option_parser`.'''
        parser = OptionParser("%prog [options] <projectname>")
        return parser

    def main(self):
        '''See `TarmacScript`.'''
        launchpad = get_launchpad_object(self.configuration,
            filename=self.filename)


class TarmacLander(TarmacScript):
    '''Tarmac landing script.

    This script handles all landing of branches.  It does the actual work for
    Tarmac.
    '''

    def __init__(self, test_mode=False):

        TarmacScript.__init__(self, test_mode)

        self.dry_run = self.options.dry_run

        if len(self.args) != 1:
            self.parser.error("Please specify a project name.")

        self.project, = self.args
        self.configuration = TarmacConfig(self.project)

        logging.basicConfig(filename=self.configuration.log_file,
            level=logging.INFO)
        self.logger = logging.getLogger('tarmac-lander')
        if self.options.debug:
            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(stderr_handler)

        # Write a pid file
        if not test_mode:
            if os.path.exists(self.configuration.PID_FILE):
                message = 'An instance of tarmac is already running.'
                self.logger.info(message)
                print message
                sys.exit()
            self.create_pid()

    def _create_option_parser(self):
        '''See `TarmacScript._create_option_parser`.'''
        parser = OptionParser("%prog [options] <projectname>")
        parser.add_option('--dry-run', action='store_true',
            help='Merge the approved branch candidates (and optionally run '
                 'their accompanying test command), and then roll back the '
                 'trunk branch to pristine state.')
        parser.add_option('--test-command', type='string', default=None,
            metavar='TEST',
            help='The test command to run after merging a branch.')
        parser.add_option('--debug', default=False, action='store_true',
            help='Print information to the screen as well as logging.')
        return parser

    def _get_reviewers(self, candidate):
        '''Get all reviewers who approved the review.'''
        return [comment.reviewer for comment in candidate.all_comments
            if comment.vote == u'Approve'].join(', ')

    def main(self):
        '''See `TarmacScript.main`.'''
        # pylint: disable-msg=W0703

        try:
            launchpad = get_launchpad_object(self.configuration)
        except HTTPError:
            message = (
                'Oops!  It appears that the OAuth token is invalid.  Please '
                'delete %(credential_file)s and re-authenticate.' %
                    {'credential_file': self.configuration.CREDENTIALS})
            self.logger.error(message)
            print message
            sys.exit()

        project = launchpad.projects[self.project]
        try:
            self.logger.info('Downloading development target:\n    %s',
                             project.development_focus.branch)
            trunk = Branch(project.development_focus.branch, create_tree=True)
        except AttributeError:
            message = (
                'Oops!  It looks like you\'ve forgotten to specify a '
                'development focus branch.  Please link your "trunk" branch '
                'to the trunk development focus.')
            self.logger.error(message)
            print message
            sys.exit()

        self.logger.debug('Looking for landing candidates')
        candidates = [entry for entry in trunk.landing_candidates
                        if entry.queue_status == u'Approved' and
                        entry.commit_message]
        if not candidates:
            self.logger.info('No branches approved to land.')
            return
        else:
            self.logger.debug('Found %s candidates to land', len(candidates))

        for candidate in candidates:

            source_branch = Branch(candidate.source_branch)

            try:
                trunk.merge(source_branch)
            except PointlessMerge:
                trunk.cleanup()
                continue

            try:
                tarmac_hooks['pre_tarmac_commit'].fire(
                    self.options, self.configuration, candidate,
                    trunk)
                if self.dry_run:
                    trunk.cleanup()
                else:
                    trunk.commit(candidate.commit_message,
                                 authors=source_branch.authors)

            except Exception, e:
                print e
                trunk.cleanup()

            tarmac_hooks['post_tarmac_commit'].fire(
                self.options, self.configuration, candidate, trunk)

