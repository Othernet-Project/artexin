"""
sessions.py: bottle sessions using MongoEngine and werkzeug session API

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import pickle
from datetime import datetime, timedelta

import mongoengine as mongo
from bson.binary import Binary
from bottle import request, response, hook
from werkzeug.contrib.sessions import SessionStore

from . import __version__ as _version, __author__ as _author

__version__ = _version
__author__ = _author
__all__ = ('Session', 'MongoSessionStore', 'session', 'cycle',)

SES_EXP = 14 * 24 * 60 * 60  # 14 days in seconds
SES_SHORT = 30 * 60  # 30 minutes in seconds
SES_COOKIE = 'cute_panda'
SES_SECRET = 'notsecret'  # FIXME: Set this using command line args in app.py


class Session(mongo.Document):
    """ Document storing session data """
    sid = mongo.StringField(
        primary_key=True,
        required=True,
        help_text='session ID')
    data = mongo.BinaryField(
        required=True,
        help_text='pickled data')
    expiry = mongo.DateTimeField(
        required=True,
        help_text='session timestamp')

    @classmethod
    def cleanup(cls):
        """ Remove obsolete sessions that are not permanent """
        cls.objects(expiry__lte=datetime.utcnow()).delete()

    @classmethod
    def by_sid(cls, sid):
        """ Retrieve session by session ID """
        return cls.objects.get(sid=sid)

    def __repr__(self):
        return '<Session: %s>' % self.sid


class MongoSessionStore(SessionStore):
    """ MongoEngine-powered session store for werkzeug """

    def save(self, session):
        """ Pickles and stores session data """
        extended = getattr(session, 'extended_session', False)
        expiry_time = SES_EXP if extended else SES_SHORT
        expiry = datetime.utcnow() + timedelta(seconds=expiry_time)
        binary = pickle.dumps(dict(session))
        sessdoc = Session(sid=session.sid, data=binary, expiry=expiry)
        sessdoc.save()

    def delete(self, session):
        """ Removes session data from database """
        try:
            sessdoc = Session.by_sid(session.sid)
            sessdoc.delete()
        except Session.DoesNotExist:
            pass

    def get(self, sid):
        """ Retrieves and unpickles session data """
        try:
            sessdoc = Session.by_sid(sid)
            return self.session_class(pickle.loads(sessdoc.data), sid, False)
        except Session.DoesNotExist:
            return self.session_class({}, sid, True)


def session(session_store):
    """ Sets up bottle sessions using Werkzeug SessionStore-compatible API

    Call this function with initailized session store object. For example::

        session_store = MongoSessionStore()
        session(session_store)

    """

    @hook('before_request')
    def session_start():
        Session.cleanup()
        sid = request.get_cookie(SES_COOKIE, secret=SES_SECRET)
        if sid:
            request.session = session_store.get(sid)
        else:
            request.session = session_store.new()
        request.session_store = session_store

    @hook('after_request')
    def session_end():
        """ Store session data

        Use this function as a 'after_request' hook like so::

            bottle.add_hook('after_request', session_end)

        """
        if request.session and request.session.should_save:
            extended = getattr(request.session, 'extended_session', False)
            # Instead of omitting max_age, we use a very short max_age for
            # 'session cookies'. The real 'session cookies' don't actually work
            # as expected in major browsers like Chrome and Firefox.
            max_age = SES_EXP if extended else SES_SHORT
            session_store.save(request.session)
            response.set_cookie(SES_COOKIE, request.session.sid, path='/',
                                secret=SES_SECRET, max_age=max_age)


def cycle():
    """ Cycle the session: copy data into a brand new session

    This function should be called whenever user's authorization level changes
    (e.g., when user logs in) to prevent session fixation attacks. It
    effectively changes the session ID without changing the session data.

    :param session: session object
    """
    sessdata = dict(request.session)
    request.session = request.session_store.new()
    request.session.update(sessdata)


