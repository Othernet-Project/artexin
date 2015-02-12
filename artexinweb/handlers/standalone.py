# -*- coding: utf-8 -*-
import datetime
import logging
import os

from artexin.extract import get_title
from artexin.pack import zipdir

from artexinweb import settings
from artexinweb.decorators import registered
from artexinweb.handlers.base import BaseJobHandler
from artexinweb.models import Job


logger = logging.getLogger(__name__)


class StandaloneHandler(BaseJobHandler):

    def is_valid_target(self, target):
        if not os.path.exists(target):
            msg = "Path: {0} not accessible.".format(target)
            logger.debug(msg)
            return False

        return True

    def handle_task(self, task, options):
        pass

    def handle_task_result(self, task, result):
        task.size = result['size']
        task.md5 = result['hash']
        task.title = result['title']
        task.images = result['images']
        task.timestamp = datetime.datetime.utcnow()
        task.mark_finished()  # implicit save


@registered(Job.STANDALONE)
def fetchable_handler(job_data):
    handler_instance = StandaloneHandler()
    handler_instance.run(job_data)
