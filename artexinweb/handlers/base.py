# -*- coding: utf-8 -*-
import logging
import time

from artexinweb.models import Job


logger = logging.getLogger(__name__)


class BaseJobHandler(object):

    def is_valid_target(self, target):
        """Checks whether the passed in target is valid.

        :param target:  URL or filesystem path string
        :returns:       bool
        """
        raise NotImplementedError()

    def is_valid_task(self, task):
        """Checks whether the passed in task should be done or not.

        :param task:  ``Task`` model instance
        :returns:     bool
        """
        return not task.is_finished

    def handle_task(self, task, options):
        """Handle the task itself and return it's results.

        :param task:     ``Task`` model instance
        :param options:  Freeform dict holding the options of the parent job.
        :returns:        Dictionary containing task results.
        """
        raise NotImplementedError()

    def handle_task_result(self, task, result, options):
        """Handle the task results.

        :param task:     ``Task`` model instance
        :param result:   Return value of ``handle_task``
        :param options:  Freeform dict holding the options of the parent job.
        :returns:        Dictionary containing task results.
        """
        raise NotImplementedError()

    def process_task(self, task, options):
        """Dispatch task and later it's results to overridden methods of the
        subclassed ``BaseJobHandler``

        :param task:     ``Task`` model instance
        :param options:  Freeform dict holding the options of the parent job.
        """
        task.mark_processing()
        start_time = time.process_time()

        if not self.is_valid_target(task.target):
            msg = "Task target {0} invalid. Marking it failed."
            logger.error(msg.format(task.target))
            task.mark_failed()
            return

        logger.info("Start processing of task {0}.".format(task.target))
        try:
            result = self.handle_task(task, options)
        except Exception:
            msg = "Unhandled exception while processing task: {0}."
            logger.exception(msg.format(task.target))
            task.mark_failed()
        else:
            elapsed_time = time.process_time() - start_time
            msg = "Task {0} finished in {1} seconds."
            logger.info(msg.format(task.target, elapsed_time))

            try:
                self.handle_task_result(task, result, options)
            except Exception:
                msg = "Unhandled exception while processing task result: {0}."
                logger.exception(msg.format(task.target))
                task.mark_failed()
            else:
                msg = "Task result handling of {0} finished."
                logger.info(msg.format(task.target))

    def run(self, job_data):
        """Gets the scheduled job instance from the database and processes it.

        :param job_data:  Deserialized message(dict) from the redis queue.
        """
        job = Job.objects.get(job_id=job_data.get('id'))
        logger.info("Begin processing {0} job: {1}".format(job.job_type,
                                                           job.job_id))
        job.mark_processing()

        for task in job.tasks:
            if self.is_valid_task(task):
                self.process_task(task, job.options)

        if any(task.is_failed for task in job.tasks):
            msg = "Processing of {0} job: {1} erred.".format(job.job_type,
                                                             job.job_id)
            logger.info(msg)
            job.mark_erred()
        else:
            msg = "Processing of {0} job: {1} succeeded.".format(job.job_type,
                                                                 job.job_id)
            logger.info(msg)
            job.mark_finished()
