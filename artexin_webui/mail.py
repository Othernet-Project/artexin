"""
email.py: sending email over SMTP using bottle templates to render messages

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

from datetime import datetime
from smtplib import SMTP, SMTP_SSL
from email.mime.text import MIMEText


from bottle import template, default_app

from . import __version__ as _version, __author__ as _author

__version__ = _version
__author__ = _author
__all__ = ('UserAction', 'User', 'restricted', 'safe_redirect', 'auth_routes')


def send(view, data, subject, to, sender=None, settings={}, conn=None,
         keep_alive=False):
    """ Send a single email message

    :param view:        template to use
    :param data:        dict containing data for the template
    :param subject:     message subject
    :param to:          recipient
    :param sender:      sender (optional)
    :param settings:    override settings (any missing keys will be filled in
                        using settings from application's configuration
    :param conn:        connection object to use instead of creaging a new one
    :param keep_alive:  whether to close the connection after sending
    :returns:           tuple containing the connection object and message
    """
    app = default_app()
    settings = settings.copy()  # Do not modify original
    settings.update(app.config['email'])
    sender = sender or settings['sender']

    # Prepare data
    data = data.copy()  # Do not modify the original
    data['subject'] = subject
    data['to'] = to
    data['sender'] = sender
    data['timestamp'] = datetime.utcnow()

    # Prepare the message
    msg = MIMEText(template(view, **data))
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to

    if not conn:
        # Establish connection
        Connection = SMTP_SSL if settings['ssl'] else SMTP
        conn = Connection(host=settings['host'], port=settings['port'])
        conn.login(settings['user'], settings['pass'])
    conn.send_message(msg)

    if not keep_alive:
        # Kill the connection
        conn.quit()

    return conn, msg
