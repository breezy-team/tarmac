#!/usr/bin/env python
# Copyright 2009 Paul Hummer
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
'''Tarmac installation script.'''

from distutils.command import clean
from distutils.core import Command, setup
import os

from tarmac import __version__


class BaseCommand(Command):
    '''A base command...'''

    user_options = []

    def initialize_options(self):
        self.cwd = None

    def finalize_options(self):
        self.cwd = os.getcwd()


class CleanCommand(clean.clean):
    '''Customized command for clean.'''

    description = 'Customized clean command'

    def run(self):
        os.system('rm -rf build _trial_temp dist')

        super(CleanCommand, self).run()


class DocCommand(BaseCommand):
    '''Command for building the docs.'''

    description = 'Build the docs'

    def run(self):
        if not os.path.exists('build/docs'):
            os.makedirs('build/docs')
        os.system(
            'rst2html docs/introduction.txt build/docs/introduction.html')
        os.system(
            'rst2html docs/writingplugins.txt build/docs/writingplugins.html')


class ReleaseCommand(BaseCommand):
    '''A command for cutting releases.'''

    description = 'Cut a release'

    def run(self):
        os.system('python setup.py sdist')
        os.system(
            'gpg --armor --sign --detach-sig `find dist -name "tarmac-*"`')


class TestCommand(BaseCommand):
    '''A Command for running the tests.'''

    description = 'Run the tests'

    def run(self):
        os.system('trial tarmac')


setup(
    author='Paul Hummer',
    author_email='Paul Hummer <paul@eventuallyanyway.com',
    cmdclass={
        'clean': CleanCommand,
        'docs': DocCommand,
        'release': ReleaseCommand,
        'test': TestCommand
        },
    name=u'tarmac',
    version=__version__,
    description=u'Tarmac - The Launchpad Lander',
    url=u'http://launchpad.net/tarmac',
    license=u'GPLv3',
    package_dir={'tarmac': 'tarmac'},
    packages=['tarmac', 'tarmac.bin', 'tarmac.plugins', 'tarmac.tests'],
    scripts=['bin/tarmac'],
    #data_files=[('share/tarmac/', ['tarmac-web']),
    #            ('share/tarmac/templates/', ['templates/index.html']),
    #            ],
    data_files=[('share/man/man1', ['docs/tarmac.1'])],
    long_description='''
        Tarmac is a series of scripts to facilitate the landing of Bazaar
        branches in Launchpad (http://edge.launchpad.net).''',
    )
