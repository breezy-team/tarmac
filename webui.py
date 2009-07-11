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

    def __init__(self):
        from tarmac.config import TarmacConfig
        config = TarmacConfig(sys.argv[2])
        self.statusfile = config.log_file

    def GET(self):
        tail = subprocess.Popen(('tail', '-n40', self.statusfile),
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE)
        output, errput = tail.communicate()
        return render.index(output, errput)


def main():
    if len(sys.argv) != 3:
        print "Please specify a port number and a project name: ./webui.py 8080 default"
        return 1
    app = web.application(urls, globals())
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
