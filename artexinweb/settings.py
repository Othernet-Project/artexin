# -*- coding: utf-8 -*-
from os import environ
from os.path import dirname, join

import bottle


WEBAPP_ROOT = dirname(__file__)
VIEW_ROOT = join(WEBAPP_ROOT, 'views')
DEV_STATIC_ROOT = join(WEBAPP_ROOT, 'static')

DEFAULT_CONFIG_PATH = join(WEBAPP_ROOT, 'confs', 'dev.ini')
CONFIG_PATH = environ.get('CONFIG_PATH', DEFAULT_CONFIG_PATH)

BOTTLE_CONFIG = bottle.ConfigDict()
BOTTLE_CONFIG.load_config(CONFIG_PATH)
