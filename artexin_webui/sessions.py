"""
sessions.py: bottle sessions using MongoEngine and werkzeug middleware

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

SES_EXP = 14 # days
SES_COOKIE = 'cute_panda'


class Session(mongo.Document):
    """ Document storing session data """
    sid = mongo.StringField(
        primary_key=True,
        required=True,
        help_text='session ID')
    data = mongo.BinaryField(
        required=True,
        help_text='pickled data')
    timestamp = mongo.DateTimeField(
        required=True,
        default=datetime.utcnow,
        help_text='session timestamp')
    permanent = mongo.BooleanField(
        default=False,
        help_text='wehether session does not expire')

    @classmethod
    def cleanup(cls):
        """ Remove obsolete sessions that are not permanent """
        exp_time = datetime.utcnow() - timedelta(days=SES_EXP)
        cls.objects(timestamp__lte=exp_time, permanent=False).delete()

    @classmethod
    def by_sid(cls, sid):
        """ Retrieve session by session ID """
        return cls.objects.get(sid=sid)


class MongoSessionStore(SessionStore):
    """ MongoEngine-powered session store for werkzeug """

    def save(self, session):
        """ Pickles and stores session data """
        binary = pickle.dumps(dict(session))
        sessdoc = Session(sid=session.sid, data=binary)
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
        sid = request.get_cookie(SES_COOKIE)
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
        if request.session.should_save:
            session_store.save(request.session)
            response.set_cookie(SES_COOKIE, request.session.sid)
