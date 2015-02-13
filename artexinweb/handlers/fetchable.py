# -*- coding: utf-8 -*-
import logging
import urllib

from artexin.pack import collect
from artexin.preprocessor_mappings import get_preps

from artexinweb import settings
from artexinweb.decorators import registered
from artexinweb.handlers.base import BaseJobHandler
from artexinweb.models import Job


logger = logging.getLogger(__name__)


class FetchableHandler(BaseJobHandler):

    def is_valid_target(self, target):
        try:
            urllib.request.urlopen(target)
        except Exception:
            msg = "URL: {0} not accessible.".format(target)
            logger.debug(msg, exc_info=True)
            return False
        else:
            return True

    def handle_task(self, task, options):
        return collect(task.target,
                       prep=get_preps(task.target),
                       base_dir=settings.BOTTLE_CONFIG['artexin.out_dir'],
                       javascript=options.get('javascript', False),
                       do_extract=options.get('extract', False))

    def handle_task_result(self, task, result, options):
        error = result.get('error')
        if error is not None:
            msg = "Error processing {0}: {1}".format(task.target, error)
            logger.error(msg)
            task.mark_failed()
            return

        task.size = result['size']
        task.md5 = result['hash']
        task.title = result['title']
        task.images = result['images']
        task.timestamp = result['timestamp']
        task.mark_finished()  # implicit save


@registered(Job.FETCHABLE)
def fetchable_handler(job_data):
    handler_instance = FetchableHandler()
    handler_instance.run(job_data)
