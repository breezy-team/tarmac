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

'''Bazaar Plugin for Tarmac.'''

from bzrlib.lazy_import import lazy_import
lazy_import(globals(), '''
from bzrlib.hooks import known_hooks

''')

known_hooks.register_lazy(
    ('tarmac.hooks.TarmacHooks', 'TarmacLander.hooks'),
    'tarmac.hooks', 'TarmacHooks')

