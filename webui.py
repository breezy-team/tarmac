#!/usr/bin/env python
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
#
# Copyright 2009 Elliot Murphy
"""Simple WSGI web application for showing the current Tarmac status."""

import sys
import subprocess
from tarmac.config import TarmacConfig
import web

urls = (
    '/', 'index'
)

render = web.template.render('templates/')

class index(object):
    """The main page of the status site."""

    def GET(self):
        # XXX I cannot figure out how to make the config object from main
        # available here.
        # statusfile = config.log_file
        from tarmac.config import TarmacConfig
        statusfile = TarmacConfig(sys.argv[2]).log_file
        print statusfile
        tail = subprocess.Popen(('tail', '-n40', statusfile),
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE)
        output, errput = tail.communicate()
        return render.index(output, errput)


def main():
    if len(sys.argv) != 3:
        print "Please specify a port number and a project name: ./webui.py 8080 default"
        return 1
    projectname = sys.argv[2]
    config = TarmacConfig(projectname)
    app = web.application(urls, globals())
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
