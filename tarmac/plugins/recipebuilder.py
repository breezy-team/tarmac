# This file is part of Tarmac.
#
# Copyright 2010 Canonical, Ltd.
#
# Tarmac is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# Tarmac is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tarmac.  If not, see <http://www.gnu.org/licenses/>.
'''Tarmac plug-in for triggering package recipe builds on Launchpad.'''
from lazr.restfulclient.errors import ResponseError
from tarmac.hooks import tarmac_hooks
from tarmac.plugins import TarmacPlugin


class PackageRecipe(TarmacPlugin):
    '''Tarmac plug-in for triggering a package recipe build.

    This plug-in checks for the package_recipe setting on the target branch
    configuration, and if found, triggers that recipe to build on Launchpad.
    '''

    def run(self, command, target):
        '''Trigger a package recipe build.'''
        try:
            self.package_recipe = target.config.package_recipe
            self.series_list = target.config.recipe_series.split(',')
        except AttributeError:
            return

        self.logger.debug('Triggering package recipe: %s' %
                          self.package_recipe)
        (owner, recipe) = self.package_recipe.split('/')
        try:
            for series in self.series_list:
                lp_recipe = command.launchpad.people[owner].getRecipe(
                    name=recipe)
                archive = lp_recipe.daily_build_archive
                distro = command.launchpad.distributions[u'Ubuntu']
                lp_series = [x for x in distro.series if x.name == series][0]
                lp_recipe.requestBuild(archive=archive,
                                       distroseries=lp_series,
                                       pocket=u'Release')
        except (KeyError, ValueError, AttributeError):
            self.logger.error('Recipe not found: %s' % self.package_recipe)
        except ResponseError, error:
            if str(error.response.status).startswith('50'):
                reason = u'{0} - OOPS: {1}'.format(
                    error.response.reason,
                    error.response.get('x-lazr-oopsid', None))
            else:
                reason = error.response.reason
            self.logger.error('Failed to request build of recipe: %s: (%s) %s',
                              self.package_recipe,
                              error.response.status, reason)

tarmac_hooks['tarmac_post_merge'].hook(PackageRecipe(),
                                       'Package recipe builder plug-in.')
