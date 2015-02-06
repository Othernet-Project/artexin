# -*- coding: utf-8 -*-
from os import environ
from os.path import dirname, join

import bottle

import controllers


default_config_path = join(dirname(__file__), 'artexin.ini')
config_path = environ.get('CONFIG_PATH', default_config_path)

application = bottle.default_app()
application.config.load_config(config_path)


if __name__ == '__main__':
    application.run(debug=True, reloader=True, host='0.0.0.0', port=9090)
