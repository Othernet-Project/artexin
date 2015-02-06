# -*- coding: utf-8 -*-
from bottle import route, jinja2_view, static_file


@route('/static/<filename:path>')
def send_static(filename):
    return static_file(filename, root='static')


@route('/')
@jinja2_view('index.html')
def index():
    return {}
