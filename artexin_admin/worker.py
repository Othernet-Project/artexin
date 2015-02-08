# -*- coding: utf-8 -*-
import os

from bottle import ConfigDict

import mongoengine

from artexin_admin import config
from artexin_admin.rqueue import RedisQueue


config_path = os.environ.get('CONFIG_PATH', config.DEFAULT_CONFIG_PATH)

config = ConfigDict()
config.load_config(config_path)

mongoengine.connect('', host=config['database.url'])
RedisQueue.setup(config)
queue = RedisQueue()


@queue.worker
def job_processor(job_data):
    print(job_data)


job_processor()
