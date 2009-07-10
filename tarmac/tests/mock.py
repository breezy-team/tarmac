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
import tempfile

from bzrlib import bzrdir


class MockLPProject(object):
    '''A mock LP Project.'''

    def __init__(self):
        self.name = b64encode(os.urandom(int(math.ceil(0.75*10))),'-_')[:10]


class MockLPBranch(object):
    '''A mock LP Branch.'''

    def __init__(self):
        temp_dir = tempfile.mkdtemp()
        self._internal_bzr_branch = bzrdir.BzrDir.create_branch_convenience(
            temp_dir)
        self.bzr_identity = self._internal_bzr_branch.base
        self.project = MockLPProject()

