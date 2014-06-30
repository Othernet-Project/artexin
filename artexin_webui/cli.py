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

import mongoengine as mongo
from bottle import default_app

from .auth import User
from .mail import send

from . import __version__ as _version, __author__ as _author

__version__ = _version
__author__ = _author
__all__ = ('create_superuser',)


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
    print("Sending message")
    conn, msg = send('email/test', {}, 'Test email', args.email_test)
    print("Sent using connection %s" % conn)
    print("Sent message %s" % msg)
    sys.exit(0)


def show_conf(args):
    app = default_app()
    pprint.pprint(app.config, indent=4)
    sys.exit(0)
