# -*- coding: utf-8 -*-
import os

from bottle import ConfigDict

import mongoengine

from artexin_admin import settings
from artexin_admin import handlers
from artexin_admin import rqueue
from artexin_admin import utils
from artexin_admin.decorators import registered


config_path = os.environ.get('CONFIG_PATH', settings.DEFAULT_CONFIG_PATH)

config = ConfigDict()
config.load_config(config_path)

mongoengine.connect('', host=config['database.url'])
rqueue.RedisQueue.setup(config)
queue = rqueue.RedisQueue()

utils.discover(handlers)


@queue.worker
def dispatcher(message):
    try:
        handlers = registered.handlers[message.pop('type', None)]
    except KeyError:
        pass
    else:
        for hander_func in handlers:
            hander_func(message)


dispatcher()
