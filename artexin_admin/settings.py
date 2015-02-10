# -*- coding: utf-8 -*-
from os.path import dirname, join


WEBAPP_ROOT = dirname(__file__)
STATIC_ROOT = join(WEBAPP_ROOT, 'static')
VIEW_ROOT = join(WEBAPP_ROOT, 'views')
DEFAULT_CONFIG_PATH = join(WEBAPP_ROOT, 'confs', 'dev.ini')
