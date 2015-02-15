# -*- coding: utf-8 -*-
import logging.config

import mongoengine

from artexinweb import handlers
from artexinweb import rqueue
from artexinweb import settings
from artexinweb import utils
from artexinweb.decorators import registered


logging.config.dictConfig(settings.LOGGING)

mongoengine.connect('', host=settings.BOTTLE_CONFIG['database.url'])
rqueue.RedisQueue.setup(settings.BOTTLE_CONFIG)
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
