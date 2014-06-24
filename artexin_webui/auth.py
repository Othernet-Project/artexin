"""
auth.py: authentication

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import os
import random
import hashlib
from functools import wraps
from urllib.parse import quote, urljoin

import pbkdf2
import bottle
import mongoengine as mongo
from bottle import request, response, template

from . import __version__ as _version, __author__ as _author
from .sessions import cycle

__version__ = _version
__author__ = _author
__all__ = ('UserAction', 'User', 'restricted', 'safe_redirect', 'auth_routes')


RNDPWCHARS = 'acdefhjkmnrtuvwxyABCDEFGJKMNPQRTUVWXY3478#@'
RNDPWLEN = 10
PWITERS = 1000
LOGIN_PATH = '/login/'


class UserAction(mongo.EmbeddedDocument):
    """ Document storing user actions """
    token = mongo.StringField(
        required=True,
        regex=r'[a-z][0-9]{10}')
    action = mongo.StringField(
        required=True,
        help_text='action type')
    data = mongo.StringField(
        help_text='action data')

    @staticmethod
    def generate_token():
        """ Generate action token """
        bstr = os.urandom(8)
        sha1 = hashlib.sha1()
        sha1.update(bstr)
        return sha1.hexdigest()[:10]


class User(mongo.Document):
    """ User document """
    is_anonymous = False
    NotUniqueError = mongo.NotUniqueError

    email = mongo.EmailField(
        unique=True,
        required=True,
        help_text='user email')
    md5 = mongo.StringField(
        required=True,
        help_text='MD5 hexdigest of the user email')
    password = mongo.StringField(
        required=True,
        help_text='encrypted password')
    superuser = mongo.BooleanField(
        default=False,
        help_text='superuser status')
    role = mongo.ListField(
        mongo.StringField,
        help_text='user role (group)')
    verified = mongo.BooleanField(
        default=False,
        help_text='whether user email is verified')
    pending = mongo.ListField(mongo.EmbeddedDocumentField(UserAction))

    def generate_password(self, length):
        """ Generate random password of specified ``length``

        The password is generated from the pool of characters defined by
        RNDPWCHARS.

        :param length:  Length of the generated password
        :returns:       Random password
        """
        return ''.join([random.choice(RNDPWCHARS) for i in range(length)])

    def set_password(self, password=None):
        """ Set a new password

        If no password is specified, a random password is automatically
        generated and assigned.

        :param password:    Clear-text password that should be set
        :returns:           Whatever password has been set
        """
        if password is None:
            password = self.generate_password(RNDPWLEN)
        self.password = pbkdf2.crypt(password, iterations=PWITERS)
        return password

    @classmethod
    def create_user(cls, email, password=None, **kwargs):
        """ Create a new user record

        :param email:       user email address
        :param password:    clear-text password
        :return:            tuple of user record and password that has been set
        """
        email = email.strip().lower()
        md5 = hashlib.md5()
        md5.update(bytes(email, 'utf-8'))
        hexdigest = md5.hexdigest()
        user = cls(email=email, md5=hexdigest, **kwargs)
        password = user.set_password(password)
        user.save()
        return user, password

    @classmethod
    def create_superuser(cls, email, password):
        user, password = cls.create_user(email=email, password=password,
                                         supeuser=True)
        assert user.superuser, 'User must be superuser'
        return user, password

    def add_action(self, action, data=None):
        """ Add a new action to the user document """
        action = UserAction(token=UserAction.generate_token(), action=action,
                            data=data)
        self.pending.push(action)

    def get_action(self, token):
        """ Find action object by email md5 and action token

        This function will return a tuple of action name and action data. If
        the action is not found, ``None`` is returned instead of action name.

        :param md5:     MD5 hexdigest of the email
        :param token:   action token
        :returns:       tuple of action name and action data
        """
        for action in self.pending:
            if action.token == token:
                return action.action, action.data
        return None, None

    @classmethod
    def authenticate(cls, email, password):
        """ Check if email-password combination match a user

        :param email:       user email address
        :param password:    user password
        :returns:           user object if authenticated, ``None`` otherwise
        """
        email = email.strip().lower()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None
        auth = user.password == pbkdf2.crypt(password, user.password)
        if auth:
            return user
        return None

    def __repr__(self):
        return '<User: %s>' % self.email


def restricted(f, role=None, allow_super=True, login=LOGIN_PATH, tpl='403'):
    """ Decorator for restricting access to routes

    The decorator expects that ``request`` object has ``session`` attribute,
    which has a dict-like interface. It will look for 'user' key within the
    ``session`` object, and if it finds none, it will assume that user is not
    loggged in.

    :param f:               decorated function
    :param role:            optionally restrict access to only certain roles
    :param allow_super:     always allow superuser
    :param login:           URL to which user should be redirected
    :param tpl:             template for '403 not authorized' page
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        redir = quote('?'.join([request.path, request.query_string]))
        user = request.session.get('user')
        if not user:
            # Not logged in, redirect to login path
            url = login + '?redir=' + redir
            redirect(url, 301)
        if (role and role in user.role) or (allow_super and user.superuser):
            # Appropriate role or superuser status, return response
            return f(*args, **kwargs)
        # Not allowed
        return template(tpl, path=request.path)

    return wrapped


def safe_redirect(url, code=302):
    """ Perform redirect without using bottle's built-in ``redirect()`` call

    This function modifies the default response object instead of creating a
    new one. It's expected that the default response is returned directly from
    the handler instead of returning dicts and strings.

    :param url:     URL to which to redirect
    """
    response.body = ""
    response.status = code
    response.set_header('Location', urljoin(request.url, url))
    return response


def auth_routes(login_path='/login/', logout_path='/logout/', redir_path='/',
                login_view='login'):
    LOGIN_PATH = login_path


    # GET /login/
    @bottle.get(login_path)
    @bottle.view(login_view, vals={'redir': redir_path}, errors={})
    def login_form():
        """ Render the login form """
        user = request.session.get('user')
        redir = request.query.get('redir', redir_path)
        if user:
            return safe_redirect(redir)  # already logged in
        return {'vals': {'redir': request.query.get('redir', redir_path)}}


    # POST /logout/
    @bottle.route(logout_path)
    def logout():
        redir = request.query.get('redir', redir_path)
        request.session_store.delete(request.session)
        request.session = None
        return safe_redirect(redir)


    # POST /login/
    @bottle.post(login_path)
    @bottle.view(login_view)
    def login():
        """ Handle login request """
        errors = {}

        # Get form data
        forms = request.forms
        redir = forms.get('redir', redir_path)
        email = forms.get('email', '')
        password = forms.get('password', '')

        # Process authentication request
        request.session['user'] = user = User.authenticate(email, password)
        if user is None:
            errors = {'_': 'Invalid email or password'}
            return {'errors': errors, 'vals': forms}
        cycle()  # changes session ID for current session
        return safe_redirect(redir)
