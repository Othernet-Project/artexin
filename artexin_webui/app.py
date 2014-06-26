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
__all__ = ('collections_form', 'collections_process',)

MODPATH = dirname(abspath(__file__))
TPLPATH = join(MODPATH, 'views')
CDIR = tempfile.gettempdir()
CPROC = 4
DEFAULT_DB = 'artexinweb'

bottle.BaseTemplate.defaults = {
    'h': helpers,
    'r': request,
}


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
        base_dir=request.app.config['collection_dir'],
        max_procs=request.app.config['collection_proc'])
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
    file_path = join(request.app.config['collection_dir'], '%s.zip' % md5)
    file_exists = exists(file_path)
    return {'page': page, 'file_path': file_path, 'exists': file_exists}


def start(port=8080, bind='127.0.0.1', debug=False, views_dir=TPLPATH,
          server='wsgiref', cdir=CDIR, cproc=CPROC, email_user=None,
          email_pwd=None, email_host=None, email_port=None, email_ssl=True,
          email_sender=''):
    """ Starts the application

    :param port:            port to listen on
    :param bind:            address to bind to
    :param debug:           enable debug mode
    :param views_dir:       directory containing views
    :param server:          WSGI server to use
    :param cdir:            directory in which to collect pages
    :param cproc:           number of child processes used for collecting pages
    :param create_sup:      whether to create superuser
    :param email_user:      user name for sending email
    :param email_host:      SMTP server host
    :param email_port:      port on the SMTP server
    :param email_ssl:       whether to use SSL to connect to SMTP server
    :param email_sender:    default sender address
    """

    app = bottle.default_app()

    bottle.TEMPLATE_PATH[0] = views_dir
    app.config['collection_dir'] = cdir
    app.config['collection_proc'] = cproc
    app.config['email'] = {
        'user': email_user,
        'pass': email_pwd,
        'host': email_host,
        'port': email_port and int(email_port),
        'ssl': email_ssl,
        'sender': email_sender,
    }

    # Add session-related hooks
    sessions.session(sessions.MongoSessionStore())

    # Set up authentication views
    auth.auth_routes('/login/')

    if debug is True:
        # Wrap in werkzeug debugger
        app = DebuggedApplication(app)

    bottle.run(app, args.server, port=args.port, host=args.bind,
               debug=args.debug, reloader=args.debug)


bottle.TEMPLATE_PATH.insert(0, TPLPATH)

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
    parser.add_argument('--cdir', help='directory in which the processed '
                        'pages are dumped (default: %s)' % CDIR,
                        default=CDIR, metavar='PATH')
    parser.add_argument('--cproc', help='number of processes to use for'
                        'collecting pages (default: %s)' % CPROC, type=int,
                        default=CPROC, metavar='N')
    parser.add_argument('--db', help='name of the MongoDB database to use '
                        '(default: %s)' % DEFAULT_DB,
                        default=DEFAULT_DB, metavar='DB')
    parser.add_argument('--email-user', help='username to use for SMTP server',
                        default=None, metavar='USER')
    parser.add_argument('--email-pass', help='password to use for SMTP server',
                        default=None, metavar='PASS')
    parser.add_argument('--email-host', help='host name of the SMTP server',
                        default=None, metavar='HOST')
    parser.add_argument('--email-port', help='port number of the SMTP server',
                        default=None, metavar='HOST')
    parser.add_argument('--email-ssl', action='store_true',
                        help='use SSL to connect to SMTP server')
    parser.add_argument('--email-sender', help="default sender address",
                        default=None, metavar='ADDR')
    parser.add_argument('--su', action='store_true',
                        help='create superuser and exit')
    parser.add_argument('--email-test',
                        help="send test email to this addres and exit",
                        default=None, metavar='ADDR')

    args = parser.parse_args(sys.argv[1:])

    # Establish database connection
    print("Connecting to database '%s' ... " % args.db, end='')
    mongoengine.connect(args.db)
    print('CONNECTED')

    # Process any tasks first
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
