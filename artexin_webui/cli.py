"""
cli.py: Command-line tasks

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import sys
import pprint
import getpass

import bottle
import mongoengine as mongo
from bottle import default_app

from lib.content_crypto import import_key, KeyImportError

from .auth import User
from .mail import send

from . import __version__ as _version, __author__ as _author

__version__ = _version
__author__ = _author
__all__ = ('configure_parser', 'process_cli',)


def configure_parser(parser):
    """ Add relevant command line switches to parser """
    parser.add_argument('--su', action='store_true',
                        help='create superuser and exit')
    parser.add_argument('--email-test',
                        help="send test email to this addres and exit",
                        default=None, metavar='ADDR')
    parser.add_argument('--key-file', help="import key file and exit",
                        default=None, metavar='PATH')


def create_superuser(args):
    print("Press ctrl-c to abort")
    try:
        email = input('Email address: ')
        password = getpass.getpass()
    except KeyboardInterrupt:
        print("Aborted")
        sys.exit(1)
    try:
        User.create_superuser(email=email, password=password)
        print("Created user")
    except mongo.errors.ValidationError:
        print("Invalid user data, please try again")
        create_superuser(args)
    except User.NotUniqueError:
        print("User already exists, please try a differnt email")
        create_superuser(args) # Loop until we have a user
    sys.exit(0)


def test_email(args):
    app = default_app()
    bottle.TEMPLATE_PATH.insert(0, app.config['artexin.views'])
    print("Sending message")
    conn, msg = send('email/test', {}, 'Test email', args.email_test)
    print("Sent using connection %s" % conn)
    print("Sent message %s" % msg)
    sys.exit(0)


def show_conf(args):
    app = default_app()
    pprint.pprint(app.config, indent=4)
    sys.exit(0)


def import_key_file(args):
    app = default_app()
    keyring = app.config['crypto.keyring']
    key = args.key_file
    try:
        import_key(key, keyring)
    except KeyImportError as err:
        print("Invalid key: %s" % err)
        sys.exit(1)
    print("Imported key '%s'" % key)


def process_cli(args):
    """ Process any command-line actions """
    if args.su:
        create_superuser(args)
    if args.email_test:
        test_email(args)
    if args.key_file:
        import_key_file(args)



