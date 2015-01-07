"""
list.py: Queries dealing with content lists
"""

from __future__ import unicode_literals

from bottle import request


def get_list(skip=0, n=20):
    """ Get ``n`` items from database, skipping first ``skip`` items

    If ``n`` is 0 or a negative number, all rows are returned.

    :param skip:    Number of rows to skip
    :param n:       Number of rows to return
    """
    db = request.db
    db.query("""
             SELECT * FROM content
             LIMIT ? OFFSET ?
             ORDER BY date DESC;
             """, n, skip)
    return db.results

