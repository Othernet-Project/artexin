# -*- coding: utf-8 -*-
import mongoengine

from artexin_admin import handlers
from artexin_admin import rqueue
from artexin_admin import settings
from artexin_admin import utils
from artexin_admin.decorators import registered


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
