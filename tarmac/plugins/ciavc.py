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

'''Tarmac plugin for enforcing a commit message format.

This code is derived from Jelmer Vernooij's CIA script for Bazaar that is found
at http://samba.org/~jelmer/bzr/cia_bzr.py and modified to fit within the needs
of Tarmac.
'''

import xmlrpclib
from xml.sax import saxutils

from tarmac.hooks import tarmac_hooks
from tarmac.plugins import TarmacPlugin
from tarmac import __version__ as version_string


class CIAVC(TarmacPlugin):
    '''Tarmac plugin for notifying CIA.vc of new commits.'''

    def __call__(self, options, configuration, candidate, trunk):
    # pylint: disable-msg=W0613,W0104,C0324

        if (configuration.cia_project and configuration.cia_server):
            cia_project = configuration.cia_project
            cia_server = configuration.cia_server
        else:
            return

        revno = trunk.branch.revno()
        files = []
        delta = trunk.branch.get_revision_delta(revno)

        [files.append(f) for (f,_x,_x) in delta.added]
        [files.append(f) for (f,_x,_x) in delta.removed]
        [files.append(f) for (_x,f,_x,_x,_x,_x) in delta.renamed]
        [files.append(f) for (f,_x,_x,_x,_x) in delta.modified]

        message = '''
<message>
  <generator>
    <name>Tarmac</name>
    <version>%(version)s</version>
    <url>http://launchpad.net/tarmac</url>
  </generator>
  <source>
    <project>%(project)s</project>
    <module>%(branch)s</module>
  </source>
  <body>
    <commit>
      <revision>%(revision)s</revision>
      <files>%(files)s</files>
      <author>%(author)s</author>
      <log>%(commit_message)s</log>
    </commit>
  </body>
</message>
        ''' % {
            'version': version_string,
            'project': cia_project,
            'branch': trunk.lp_branch.bzr_identity,
            'revision': revno,
            'files': '\n'.join([
                '<file>%s</file>' % saxutils.escape(f) for f in files]),
            'author': saxutils.escape(
                candidate.source_branch.owner.display_name),
            'commit_message': saxutils.escape(candidate.commit_message)}

        print "Updating cvs.vc for project " + cia_project
        xmlrpclib.ServerProxy(cia_server).hub.deliver(message)

tarmac_hooks['post_tarmac_commit'].hook(CIAVC(), 'CIA.vc plugin.')

