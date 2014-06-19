"""
app.py: main web UI module

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import time
import tempfile
from os.path import abspath, dirname, join

import bottle
from bottle import request
from werkzeug.debug import DebuggedApplication

from artexin.batch import batch

import artexin_webui


__version__ = artexin_webui.__version__
__author__ = artexin_webui.__author__
__all__ = ('collections_form', 'collections_process',)

MODPATH = dirname(abspath(__file__))
TPLPATH = join(MODPATH, 'views')
CDIR = tempfile.gettempdir()
CPROC = 8
DEFAULT_DB = 'artexinweb'

app = bottle.app()

# Configure the application
app.config.update({
    'collection_dir': CDIR,
    'collection_proc': CPROC,
})

# GET /collections/
@bottle.get('/collections/')
@bottle.view('collection_form')
def collections_form():
    """ Handles display of page collection queue UI """
    return {}


# POST /collections/
@bottle.post('/collections/')
@bottle.view('collection_result')
def collections_process():
    """ Process URLs that were passed through the collection form """
    urls = request.forms.get('urls')
    if urls is None:
        return "no URLs given"
    start = time.time()
    urls = list(set([url.strip() for url in urls.strip().split('\n')]))
    results = batch(urls, base_dir=request.app.config['collection_dir'],
                    max_procs=request.app.config['collection_proc'])
    return {
        'metadata': results,
        'time': time.time() - start
    }


bottle.TEMPLATE_PATH.insert(0, TPLPATH)

if __name__ == '__main__':
    import sys
    import argparse

    import mongoengine


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
    parser.add_argument('--cdir', help='directory in which the processed '
                        'pages are dumped (default: %s)' % CDIR,
                        default=CDIR, metavar='PATH')
    parser.add_argument('--cproc', help='number of processes to use for'
                        'collecting pages (default: %s)' % CPROC, type=int,
                        default=CPROC, metavar='N')
    parser.add_argument('--db', help='name of the MongoDB database to use '
                        '(default: %s)' % DEFAULT_DB,
                        default=DEFAULT_DB, metavar='DB')
    args = parser.parse_args(sys.argv[1:])

    bottle.TEMPLATE_PATH[0] = args.views
    app.config['collection_dir'] = args.cdir
    app.config['collection_procs'] = args.cproc
    app.config['mongodb'] = args.db

    mongoengine.connect(args.db)

    print("Collection directory: %s" % args.cdir)
    print("Collection processes: %s" % args.cproc)
    print("Connected to DB:      %s" % args.db)

    if args.debug is True:
        # Wrap in werkzeug debugger
        app = DebuggedApplication(app)

    # Run the app using cherrypy
    bottle.run(app, args.server, port=args.port, host=args.bind,
               debug=args.debug, reloader=args.debug)
