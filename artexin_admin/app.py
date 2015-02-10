# -*- coding: utf-8 -*-
import bottle
import mongoengine

from artexin_admin import controllers
from artexin_admin import rqueue
from artexin_admin import settings
from artexin_admin import utils


bottle.TEMPLATE_PATH.insert(0, settings.VIEW_ROOT)

application = bottle.default_app()
application.config.load_dict(settings.BOTTLE_CONFIG)

mongoengine.connect('', host=application.config['database.url'])
rqueue.RedisQueue.setup(application.config)

utils.discover(controllers)


if __name__ == '__main__':
    application.run(debug=True, reloader=True, host='0.0.0.0', port=9090)
