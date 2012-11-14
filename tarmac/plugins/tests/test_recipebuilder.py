# Copyright 2010 Canonical, Ltd.
#
# This file is part of Tarmac.
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
"""Tests for the RecipeBuilder plug-in."""

from tarmac.plugins.recipebuilder import PackageRecipe
from tarmac.tests import TarmacTestCase
from tarmac.tests.mock import Thing


class RecipeBuilderTests(TarmacTestCase):
    """Test the Recipe Builder."""

    def setUp(self):
        """Set up data for the tests."""
        super(RecipeBuilderTests, self).setUp()
        self.proposal = Thing()
        self.plugin = PackageRecipe()

    def getRecipe(self, name=None):
        """Fake getRecipe call for testing."""
        self.assertEqual(name, u'recipe')
        recipe = Thing(requestBuild=self.requestBuild,
                       daily_build_archive=u'ppa')
        return recipe

    def requestBuild(self, archive=None, distroseries=None, pocket=None):
        """Fake requestBuild call for testing."""
        self.assertTrue(distroseries.name in [u'current', u'previous'])
        self.assertEqual(archive, u'ppa')

    def test_run(self):
        """Test that the plug-in runs correctly."""
        launchpad = Thing(
            people={u'owner': Thing(getRecipe=self.getRecipe)},
            distributions={u'Ubuntu': Thing(series=[Thing(name=u'current'),
                                                    Thing(name=u'previous')])})
        command = Thing(launchpad=launchpad)
        target = Thing(config=Thing(package_recipe=u'owner/recipe',
                                    recipe_series=u'current,previous'))
        self.plugin.run(command=command, target=target, success_count=0)
