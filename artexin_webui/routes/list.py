"""
list.py: Content list
"""

from __future__ import unicode_literals

from bottle import view

from ..db import list


#@view('list')
def show_list():
    return list.get_list()
