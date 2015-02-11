# -*- coding: utf-8 -*-
import datetime
import logging
import urllib
import time

from artexin.pack import collect
from artexin.preprocessor_mappings import get_preps

from artexinweb import settings
from artexinweb.decorators import registered
from artexinweb.models import Job


logger = logging.getLogger(__name__)


class JobHandler(object):

    def is_valid_url(self, url):
        """Checks whether the passed in url is accessible.

        :param url:  The target URL
        :returns:    bool
        """
        try:
            urllib.request.urlopen(url)
        except Exception:
            logger.debug("URL: {0} not accessible.".format(url), exc_info=True)
            return False
        else:
            return True

    def is_valid_task(self, task):
        """Checks whether the passed in task should be done or not.

        :param task:  ``Task`` model instance
        :returns:     bool
        """
        if task.is_finished:
            return False

        return self.is_valid_url(task.url)

    def handle_task_result(self, task, result):
        error = result.get('error')
        if error is not None:
            logger.error("Error processing {0}: {1}".format(task.url, error))
            task.mark_failed()
            return

        task.size = result['size']
        task.md5 = result['hash']
        task.title = result['title']
        task.images = result['images']
        task.timestamp = datetime.datetime.utcnow()
        task.mark_finished()  # implicit save

    def process_task(self, task, options):
        """Process task instance and save results to the database.

        :param task:  ``Task`` model instance
        """
        task.mark_processing()
        start_time = time.process_time()
        try:
            meta = collect(task.url,
                           prep=get_preps(task.url),
                           base_dir=settings.BOTTLE_CONFIG['artexin.out_dir'],
                           javascript=options.get('javascript', False),
                           do_extract=options.get('extract', False))
        except Exception:
            msg = "Unhandled exception while processing: {0}.".format(task.url)
            logger.exception(msg)
            task.mark_failed()
        else:
            elapsed_time = time.process_time() - start_time
            msg = "Task {0} finished in {1} seconds."
            logger.debug(msg.format(task.url, elapsed_time))

            self.handle_task_result(task, meta)

    def run(self, job_data):
        """Gets the scheduled job instance from the database and processes it.

        :param job_data:  Deserialized message(dict) from the redis queue.
        """
        job = Job.objects.get(job_id=job_data.get('id'))
        job.mark_processing()

        for task in job.tasks:
            if self.is_valid_task(task):
                self.process_task(task, job.options)

        if any(task.is_failed for task in job.tasks):
            job.mark_erred()
        else:
            job.mark_finished()


@registered('job')
def job_handler(job_data):
    handler_instance = JobHandler()
    handler_instance.run(job_data)
