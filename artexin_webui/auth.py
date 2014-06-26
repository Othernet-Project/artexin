"""
auth.py: authentication

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import os
import re
import time
import random
import hashlib
from functools import wraps
from email.utils import parseaddr
from datetime import datetime, timedelta
from urllib.parse import quote, urljoin

import pbkdf2
import bottle
import mongoengine as mongo
from bottle import request, response, redirect, template

from . import __version__ as _version, __author__ as _author
from .sessions import cycle
from .mail import send

__version__ = _version
__author__ = _author
__all__ = ('UserAction', 'User', 'restricted', 'safe_redirect', 'auth_routes')


RNDPWCHARS = 'acdefhjkmnrtuvwxyABCDEFGJKMNPQRTUVWXY3478#@'
RNDPWLEN = 10
PWITERS = 1000
LOGIN_PATH = '/login/'
VERIFY_SUBJECT = 'ArtExIn access URL (%s)'
RESET_SUBJECT = 'ArtExIn password reset (%s)'
TIMESTAMP = '%a %d %b at %H:%M:%S UTC'
TOKEN_FORMAT = '[0-9a-f]{10}'
ACTION_EXPIRY = 3 * 60  # 3 minutes in seconds
RESET_EXPIRY = 24 * 60 * 60  # 1 day in seconds
SES_USER_KEY = 'user'


class LoginDetails(mongo.EmbeddedDocument):
    timestamp = mongo.DateTimeField(
        default=datetime.utcnow(),
        help_text='login timestamp')
    ip_address = mongo.StringField(
        required=True,
        help_text='IP address')

    def __repr__(self):
        return '<LoginDetails %s from %s>' % (self.timestamp, self.ip_address)


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
    logins = mongo.ListField(
        mongo.EmbeddedDocumentField(LoginDetails),
        help_text='login history')

    def generate_password(self, length):
        """ Generate random password of specified ``length``

        The password is generated from the pool of characters defined by
        RNDPWCHARS.

        :param length:  Length of the generated password
        :returns:       Random password
        """
        return ''.join([random.choice(RNDPWCHARS) for i in range(length)])

    @staticmethod
    def encrypt_password(password):
        """ Encrypts the password using PBKDF2 """
        return pbkdf2.crypt(password, iterations=PWITERS)

    def set_password(self, password=None):
        """ Set a new password

        If no password is specified, a random password is automatically
        generated and assigned.

        :param password:    Clear-text password that should be set
        :returns:           Whatever password has been set
        """
        if password is None:
            password = self.generate_password(RNDPWLEN)
        self.password = self.encrypt_password(password)
        return password

    def add_action(self, action, data=None, expiry=ACTION_EXPIRY):
        """ Add a new action to the user document """
        expiry = datetime.utcnow() + timedelta(seconds=expiry)
        action = UserAction(
            user=self,
            token=UserAction.generate_token(),
            action=action,
            expiry=expiry,
            data=data)
        action.save()
        return action

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


class UserAction(mongo.Document):
    """ Document storing user actions """
    user = mongo.ReferenceField(
        User,
        help_text='user to which this action belongs')
    token = mongo.StringField(
        required=True,
        regex=TOKEN_FORMAT)
    action = mongo.StringField(
        required=True,
        help_text='action type')
    expiry = mongo.DateTimeField(
        required=True,
        help_text='expiry timestamp')
    data = mongo.DictField(
        help_text='action data')
    timestamp = mongo.DateTimeField(
        default=datetime.utcnow(),
        help_text='creation timestamp')

    @staticmethod
    def generate_token():
        """ Generate action token """
        bstr = os.urandom(8)
        sha1 = hashlib.sha1()
        sha1.update(bstr)
        return sha1.hexdigest()[:10]

    @classmethod
    def get_action(cls, token):
        """ Find action related to token and return user and action data

        The ``DoesNotExist`` exception will be raised if there is no matching
        token.

        :param token:   token
        :returns:       tuple containing user document, action name, and data
        """
        cls.cleanup()
        action_obj = cls.objects.get(token=token)
        user = action_obj.user
        action = action_obj.action
        data = action_obj.data
        action_obj.delete()
        return user, action, data

    @classmethod
    def cleanup(cls):
        """ Removes all expired action tokens """
        cls.objects(expiry__lt=datetime.utcnow()).delete()

    def __repr__(self):
        return '<UserAction %s>' % self.token



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


def restricted(f, role=None, allow_super=True, login=LOGIN_PATH, tpl='403'):
    """ Decorator for restricting access to routes

    The decorator expects that ``request`` object has ``session`` attribute,
    which has a dict-like interface. It will look for ``SES_USER_KEY`` key
    within the ``session`` object, and if it finds none, it will assume that
    user is not loggged in.

    :param f:               decorated function
    :param role:            optionally restrict access to only certain roles
    :param allow_super:     always allow superuser
    :param login:           URL to which user should be redirected
    :param tpl:             template for '403 not authorized' page
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        redir = quote('?'.join([request.path, request.query_string]))
        user = request.session.get(SES_USER_KEY)
        if user is None:
            # Not logged in, redirect to login path
            url = LOGIN_PATH + '?redir=' + redir
            redirect(url, 301)
        role_allowed = role in user.role if role else True
        if role_allowed or (allow_super and user.superuser):
            # Appropriate role or superuser status, return response
            return f(*args, **kwargs)
        # Not allowed
        return template(tpl, path=request.path)
    return wrapped


def auth_routes(login_path='/login/', logout_path='/logout/', redir_path='/',
                login_view='login', login_failed_view='login_failed',
                check_view='check', reset_path='/reset/', reset_view='reset',
                reset_check_view='reset_check',
                reset_failed_view='reset_failed'):
    LOGIN_PATH = login_path
    token_path_fragment = '<token:re:%s>' % TOKEN_FORMAT

    # GET /login/
    @bottle.get(login_path)
    @bottle.view(login_view, vals={'redir': redir_path}, errors={})
    def login_form():
        """ Render the login form """
        user = request.session.get(SES_USER_KEY)
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
        remember = forms.get('remember', 's')
        password = forms.get('password', '')

        # Process authentication request
        user = User.authenticate(email, password)
        if user is None:
            errors = {'_': 'Invalid email or password'}
            return {'errors': errors, 'vals': forms}
        action = user.add_action('verify', {'redir': redir, 'rem': remember})
        subject = VERIFY_SUBJECT % datetime.utcnow().strftime(TIMESTAMP)
        data = {'token': action.token, 'expiry': action.expiry}
        send('email/verify', data, subject, user.email)
        return safe_redirect(login_path + 'check')

    # GET /login/check
    @bottle.get(login_path + 'check')
    @bottle.view(check_view)
    def login_check():
        """ Show check email page for two-step verfication """
        return {}

    # GET /login/<token>
    @bottle.get(login_path + token_path_fragment)
    @bottle.view(login_failed_view)
    def login_verify(token):
        try:
            user, action, data = UserAction.get_action(token)
        except UserAction.DoesNotExist:
            return {}

        if action != 'verify':
            return {}  # Wrong action

        login_details = LoginDetails(timestamp=datetime.utcnow(),
                                     ip_address=request.remote_addr)
        user.logins.append(login_details)
        if not user.verified:
            user.verified = True
        user.save()

        # Log the user in
        request.session[SES_USER_KEY] = user
        cycle()
        request.session.extended_session = data['rem'] == 'r'
        return safe_redirect(data.get('redir', redir_path))

    # GET /reset/
    @bottle.get(reset_path)
    @bottle.view(reset_view, vals={}, errors={})
    def reset_form():
        """ Show reset password form """
        return {}

    # POST /reset/
    @bottle.post(reset_path)
    @bottle.view(reset_view)
    def reset():
        """ Handle reset request """
        errors = {}

        # Get form data
        forms = request.forms
        email = forms.get('email', '').strip().lower()
        password = forms.get('password', '').strip()
        confirm = forms.get('confirm', '').strip()
        user = request.session.get('user')

        # Validate
        if not user:
            _, email = parseaddr(email)
            if '@' not in email:
                errors['email'] = 'Please type in a valid email address'
        else:
            email = user.email
        if password == '':
            errors['password'] = 'Password cannot be empty'
        if confirm == '':
            errors['confirm'] = 'Please retype the password'
        if password != confirm:
            errors['_'] = 'Passwords do not match'

        if errors:
            return {'vals': forms, 'errors': errors}

        if not user:
            # Find user with that email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Pretend to be sending an email
                time.sleep(random.randrange(5, 20))
                return safe_redirect(reset_path + 'check')

        encrypted = User.encrypt_password(password)

        # Generate action
        action = user.add_action('reset', {'pw': encrypted},
                                 expiry=RESET_EXPIRY)
        subject = RESET_SUBJECT % datetime.utcnow().strftime(TIMESTAMP)
        data = {'token': action.token, 'expiry': action.expiry}
        send('email/reset', data, subject, user.email)
        return safe_redirect(reset_path + 'check')

    @bottle.get(reset_path + 'check')
    @bottle.view(reset_check_view)
    def reset_check():
        """ Show check email page for password reset """
        return {}


    @bottle.get(reset_path + token_path_fragment)
    @bottle.view(reset_failed_view)
    def reset_done(token):
        try:
            user, action, data = UserAction.get_action(token)
        except UserAction.DoesNotExist:
            return {}

        if action != 'reset':
            return {}

        # Set the password for real
        user.password = data['pw']
        user.save()

        # Force log-out
        logout()

        return safe_redirect(login_path)
