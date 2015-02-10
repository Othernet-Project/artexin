# -*- coding: utf-8 -*-
from bottle import route, jinja2_view, static_file

from artexin_admin import settings


@route('/static/<filename:path>')
def send_static(filename):
    return static_file(filename, root=settings.STATIC_ROOT)


@route('/')
@jinja2_view('index.html')
def index():
    return {}
