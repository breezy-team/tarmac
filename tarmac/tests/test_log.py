# Copyright 2013 Canonical Ltd.
#
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

'''Tests for tarmac.log'''
from io import StringIO
import os
import sys

from tarmac.tests import TarmacTestCase
from tarmac import log


class TestSetupLogging(TarmacTestCase):

    def test_ensure_log_dir_creates(self):
        log_file = 'foo/bar.log'
        self.assertFalse(os.path.exists('foo'))
        log.ensure_log_dir(log_file)
        self.assertTrue(os.path.isdir('foo'))

    def test_ensure_log_dir_existing(self):
        log_file = 'foo/bar.log'
        os.mkdir('foo')
        # No error should be raised
        log.ensure_log_dir(log_file)
        self.assertTrue(os.path.isdir('foo'))

    def test_ensure_log_dir_cannot_create(self):
        stderr = StringIO()
        self.patch(sys, 'stderr', stderr)
        os.mkdir('foo')
        os.chmod('foo', 0o500)
        log_file = 'foo/baz/bar.log'
        log.ensure_log_dir(log_file)
        self.assertFalse(os.path.exists('foo/baz'))
        os.chmod('foo', 0o700)
        self.assertContainsRe(stderr.getvalue(),
            'Failed to create logging directory: .*foo/baz')

    def test_ensure_log_dir_handles_no_file(self):
        # No error should be raised
        log.ensure_log_dir(None)

    def test_set_up_logging_ensures_directory(self):
        class WasCalled(Exception):
            pass
        def was_called(log_file):
            raise WasCalled()
        self.patch(log, 'ensure_log_dir', was_called)
        # We raise an exception, because we don't actually want to mutate the
        # logging state, just assert that we are calling the function. So we
        # raise an exception to exit set_up_logging early.
        self.assertRaises(WasCalled, log.set_up_logging, {'log_file': 'foo'})
