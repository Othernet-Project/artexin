"""
cli.py: Command-line tasks

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import sys
import getpass

import mongoengine as mongo

from .auth import User

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

