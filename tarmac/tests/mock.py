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

'''Mock objects for Tarmac!'''
from base64 import b64encode
import math
import os

from bzrlib.bzrdir import BzrDir

from tarmac.bin.commands import TarmacCommand


class MockLPProject(object):
    '''A mock LP Project.'''

    def __init__(self):
        self.name = b64encode(
            os.urandom(int(math.ceil(0.75 * 10))), '-_')[:10]


class MockLPBranch(object):
    '''A mock LP Branch.'''

    def __init__(self, tree_dir, source_branch=None):
        self.tree_dir = tree_dir
        os.makedirs(tree_dir)
        if source_branch:
            source_dir = source_branch._internal_bzr_branch.bzrdir
            bzrdir = source_dir.sprout(tree_dir)
            self._internal_tree, self._internal_bzr_branch = \
                    bzrdir.open_tree_or_branch(tree_dir)
            self.revision_count = source_branch.revision_count
        else:
            self._internal_bzr_branch = BzrDir.create_branch_convenience(
                tree_dir)
            self.revision_count = 0
        self.bzr_identity = self._internal_bzr_branch.base[:-1]
        self.project = MockLPProject()


class cmd_mock(TarmacCommand):
    '''A mock command.'''

    def run(self):
        """Just a dummy command that does nothing."""


class MockModule(object):
    """A mock module."""

    def __init__(self):
        self.__dict__['cmd_mock'] = cmd_mock


class Thing(object):
    """Quickly create an object with given attributes."""

    def __init__(self, **names):
        self.__dict__.update(names)
