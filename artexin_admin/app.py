# -*- coding: utf-8 -*-
import os

import bottle
import mongoengine

import config
import controllers
import rqueue
import utils


bottle.TEMPLATE_PATH.insert(0, config.VIEW_ROOT)

config_path = os.environ.get('CONFIG_PATH', config.DEFAULT_CONFIG_PATH)

application = bottle.default_app()
application.config.load_config(config_path)

mongoengine.connect('', host=application.config['database.url'])
rqueue.RedisQueue.setup(application.config)

utils.discover(controllers)


if __name__ == '__main__':
    application.run(debug=True, reloader=True, host='0.0.0.0', port=9090)
