"""
app.py: main web UI module

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

from os.path import abspath, dirname, join

import bottle
from werkzeug.debug import DebuggedApplication

import artexin_webui


__version__ = artexin_webui.__version__
__author__ = artexin_webui.__author__
__all__ = ('collection_form',)

MODPATH = dirname(abspath(__file__))
TPLPATH = join(MODPATH, 'views')


@bottle.get('/collections/')
@bottle.view('collection_form')
def collection_form():
    """ Handles display of page collection queue UI """
    return {}


bottle.TEMPLATE_PATH.insert(0, TPLPATH)
wsgiapp = bottle.app()

if __name__ == '__main__':
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='start the ArtExIn Web UI')
    parser.add_argument('--port', '-p', type=int, help='port at which the '
                        'WebUI will listen (default: 8080)', default=8080,
                        metavar='PORT')
    parser.add_argument('--bind', '-b', help='address to which the Web UI '
                        'will bind (default: 127.0.0.1', default='127.0.0.1',
                        metavar='ADDR')
    parser.add_argument('--debug', '-d', help='start in debug mode',
                        action='store_true')
    parser.add_argument('--views', help='view directory (default: '
                        '%s)' % TPLPATH, default=TPLPATH, metavar='PATH')
    parser.add_argument('--server', help='WSGI server to use as backend '
                        '(default: wsgiref)', default='wsgiref',
                        metavar='SRV')
    args = parser.parse_args(sys.argv[1:])

    if args.debug is True:
        # Wrap in werkzeug debugger
        wsgiapp = DebuggedApplication(wsgiapp)

    bottle.TEMPLATE_PATH[0] = args.views

    # Run the app using cherrypy
    bottle.run(wsgiapp, args.server, port=args.port, host=args.bind,
               debug=args.debug, reloader=args.debug)
