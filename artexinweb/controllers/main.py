# -*- coding: utf-8 -*-
from bottle import get, static_file

from artexinweb import settings


@get('/static/<filename:path>')
def send_static(filename):
    return static_file(filename, root=settings.DEV_STATIC_ROOT)
