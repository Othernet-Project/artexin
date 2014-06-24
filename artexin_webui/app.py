"""
app.py: main web UI module

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import time
import getpass
import tempfile
from os.path import abspath, dirname, join

import bottle
from bottle import request
from werkzeug.debug import DebuggedApplication

import artexin_webui
from artexin_webui.schema import *
from artexin_webui import helpers
from artexin_webui import sessions
from artexin_webui import auth
from artexin_webui import cli


__version__ = artexin_webui.__version__
__author__ = artexin_webui.__author__
__all__ = ('collections_form', 'collections_process',)

MODPATH = dirname(abspath(__file__))
TPLPATH = join(MODPATH, 'views')
CDIR = tempfile.gettempdir()
CPROC = 4
DEFAULT_DB = 'artexinweb'

app = bottle.app()

# Configure the application
app.config.update({
    'collection_dir': CDIR,
    'collection_proc': CPROC,
})

bottle.BaseTemplate.defaults = {
    'h': helpers,
}


# GET /collections/
@bottle.get('/collections/')
@bottle.view('collection_form', h=helpers)
def collections_form():
    """ Handles display of page collection queue UI """
    return {}


# POST /collections/
@bottle.post('/collections/')
def collections_process():
    """ Process URLs that were passed through the collection form """
    urls = request.forms.get('urls')
    if urls is None:
        return "no URLs given"
    urls = list(set([url.strip() for url in urls.strip().split('\n')]))
    batch = Batch.process_urls(
        urls,
        base_dir=request.app.config['collection_dir'],
        max_procs=request.app.config['collection_proc'])
    bottle.redirect('/batches/%s' % batch.id)


# GET /collections/<batch_id>
@bottle.get('/batches/<batch_id>')
@bottle.view('batch')
def collection_result(batch_id):
    """ Display pages belonging to a single batch """
    try:
        return {
            'batch': Batch.objects.get(batch_id__startswith=batch_id)
        }
    except Batch.DoesNotExist:
        bottle.abort(404, 'Not found')


# GET /batches/
@bottle.get('/batches/')
@bottle.view('batches')
def batches_list():
    return {'batches': Batch.objects().order_by('-finished')}


# GET /pages/
@bottle.get('/pages/')
@bottle.view('pages')
def pages_list():
    return {'pages': Page.objects.order_by('-timestamp')}


# Set up authentication views
auth.auth_routes('/login/')


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
    parser.add_argument('--su', action='store_true',
                        help='create superuser and exit')
    args = parser.parse_args(sys.argv[1:])

    bottle.TEMPLATE_PATH[0] = args.views
    app.config['collection_dir'] = args.cdir
    app.config['mongodb'] = args.db

    mongoengine.connect(args.db)

    if args.su:
        cli.create_superuser(args)

    # Add session-related hooks
    sessions.session(sessions.MongoSessionStore())

    print("Collection directory: %s" % args.cdir)
    print("Collection processes: %s" % args.cproc)
    print("Connected to DB:      %s" % args.db)

    if args.debug is True:
        # Wrap in werkzeug debugger
        app = DebuggedApplication(app)

    # Run the app using cherrypy
    bottle.run(app, args.server, port=args.port, host=args.bind,
               debug=args.debug, reloader=args.debug)
