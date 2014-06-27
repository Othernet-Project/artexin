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
from os.path import abspath, dirname, join, exists

import bottle
import mongoengine
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

MODPATH = dirname(abspath(__file__))
TPLPATH = join(MODPATH, 'views')
CONFPATH = join(dirname(MODPATH), 'conf', 'artexin.ini')
CDIR = tempfile.gettempdir()
CPROC = 4
DEFAULT_DB = 'artexinweb'

bottle.BaseTemplate.defaults = {
    'h': helpers,
    'r': request,
}

app = bottle.default_app()


# GET /
@bottle.get('/')
@bottle.view('home')
@auth.restricted
def home():
    return {}


# GET /collections/
@bottle.get('/collections/')
@bottle.view('collection_form', h=helpers)
@auth.restricted
def collections_form():
    """ Handles display of page collection queue UI """
    return {}


# POST /collections/
@bottle.post('/collections/')
@auth.restricted
def collections_process():
    """ Process URLs that were passed through the collection form """
    urls = request.forms.get('urls')
    if urls is None:
        return "no URLs given"
    urls = list(set([url.strip() for url in urls.strip().split('\n')]))
    batch = Batch.process_urls(
        urls,
        base_dir=request.app.config['artex.directory'],
        max_procs=request.app.config['artex.processes'])
    bottle.redirect('/batches/%s' % batch.id)


# GET /collections/<batch_id>
@bottle.get('/batches/<batch_id>')
@bottle.view('batch')
@auth.restricted
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
@auth.restricted
def batches_list():
    return {'batches': Batch.objects().order_by('-finished')}


# GET /pages/
@bottle.get('/pages/')
@bottle.view('pages')
@auth.restricted
def pages_list():
    return {'pages': Page.objects.order_by('-timestamp')}


# GET /pages/<page_id>
@bottle.get('/pages/<page_id>')
@bottle.view('page')
@auth.restricted
def page(page_id):
    try:
        page = Page.objects.get(md5=page_id)
    except Page.DoesNotExist:
        bottle.abort(404)
    md5 = page.md5
    file_path = join(request.app.config['artex.directory'], '%s.zip' % md5)
    file_exists = exists(file_path)
    return {'page': page, 'file_path': file_path, 'exists': file_exists}


def start():
    """ Starts the application

    :param conf_path:   path to configuration file
    """

    bottle.TEMPLATE_PATH[0] = app.config['artexin.views']

    # Add session-related hooks
    sessions.session(sessions.MongoSessionStore())

    # Set up authentication views
    auth.auth_routes('/login/')

    bottle.run(app, server=app.config['artexin.server'],
               host=app.config['artexin.bind'],
               port=app.config['artexin.port'],
               reloader=app.config['artexin.debug'],
               debug=app.config['artexin.debug'],)


bottle.TEMPLATE_PATH.insert(0, TPLPATH)

if __name__ == '__main__':
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='start the ArtExIn Web UI')
    parser.add_argument('--conf', '-c', help='path to configuration file',
                        metavar='FILE', default=CONFPATH)
    parser.add_argument('--debug-conf', help='show configuration and exit',
                         action='store_true')
    parser.add_argument('--su', action='store_true',
                        help='create superuser and exit')
    parser.add_argument('--email-test',
                        help="send test email to this addres and exit",
                        default=None, metavar='ADDR')

    args = parser.parse_args(sys.argv[1:])
    app.config.load_config(args.conf)

    # Establish database connection
    mongoengine.connect(app.config['artexin.database'])
    print("Connected to database")

    # Process any tasks first
    if args.debug_conf:
        cli.show_conf(args)
    if args.su:
        cli.create_superuser(args)
    if args.email_test:
        cli.test_email(args)

    # Start the application
    print('Starting application')
    start(port=args.port, bind=args.bind, debug=args.debug,
          views_dir=args.views, server=args.server, cdir=args.cdir,
          cproc=args.cproc, email_user=args.email_user,
          email_pwd=args.email_pass, email_host=args.email_host,
          email_port=args.email_port, email_ssl=args.email_ssl,
          email_sender=args.email_sender)
