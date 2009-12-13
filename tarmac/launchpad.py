# Copyright 2009 Paul Hummer
# Copyright 2009 Canonical Ltd.
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

'''Utilities for Tarmac, mostly dealing with Launchpad.'''
import os

from launchpadlib.launchpad import (Credentials, Launchpad, EDGE_SERVICE_ROOT,
    STAGING_SERVICE_ROOT)


def get_launchpad_object(config, filename=None, staging=False):
    '''Return an autheticated launchpad API object.'''
    if not filename:
        filename = config.CREDENTIALS

    if staging:
        SERVICE_ROOT = STAGING_SERVICE_ROOT
    else:
        SERVICE_ROOT = EDGE_SERVICE_ROOT

    # XXX: rockstar - 2009 Dec 13 - Ideally, we should be using
    # Launchpad.login_with, but currently, it doesn't support the option of
    # putting the credentials file somewhere other than where the cache goes,
    # and that's kinda nasty (and a security issue according to Kees).
    if not os.path.exists(filename):
        launchpad = Launchpad.get_token_and_login(
            'Tarmac', SERVICE_ROOT, config.CACHE_HOME)
        launchpad.credentials.save(file(filename, 'w'))
    else:
        credentials = Credentials()
        credentials.load(open(filename))
        launchpad = Launchpad(credentials, SERVICE_ROOT, config.CACHE_HOME)

    return launchpad
