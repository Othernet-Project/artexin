# -*- coding: utf-8 -*-
import datetime
import hashlib

import mongoengine

from artexinweb import rqueue


MD5_LENGTH = 32


class Task(mongoengine.Document):
    """Tasks are the smallest unit of work, which contain an exact target that
    needs to be processed."""
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"
    FINISHED = "FINISHED"
    STATUSES = (
        (QUEUED, "Queued"),
        (PROCESSING, "Processing"),
        (FAILED, "Failed"),
        (FINISHED, "Finished"),
    )

    meta = {
        'indexes': ['md5']
    }

    job_id = mongoengine.StringField(required=True,
                                     max_length=MD5_LENGTH,
                                     min_length=MD5_LENGTH,
                                     help_text="ID of parent Job.")
    target = mongoengine.StringField(required=True,
                                     help_text="Target URL or filesystem path")
    domain = mongoengine.StringField(help_text="URL Domain or outernet")
    md5 = mongoengine.StringField(max_length=MD5_LENGTH,
                                  min_length=MD5_LENGTH,
                                  help_text="MD5 hexdigest of target.")
    title = mongoengine.StringField(help_text="Processed page title.")
    size = mongoengine.IntField(min_value=0,
                                help_text="Size of page in bytes.")
    images = mongoengine.IntField(min_value=0,
                                  help_text="Number of images on the page.")
    timestamp = mongoengine.DateTimeField(help_text="End time of task.")
    status = mongoengine.StringField(choices=STATUSES,
                                     default=QUEUED,
                                     help_text="Job status.")

    @classmethod
    def create(cls, job_id, target):
        """Create a new task for the passed in target.

        :param job_id:  The string ID of the parent job instance
        :param target:  The target URL or filesystem path
        :returns:       ``Task`` instance
        """
        task = cls(job_id=job_id, target=target)
        task.save()
        return task

    @property
    def is_finished(self):
        return self.status == self.FINISHED

    @property
    def is_failed(self):
        return self.status == self.FAILED

    def mark_processing(self):
        self.status = self.PROCESSING
        self.save()

    def mark_failed(self):
        self.status = self.FAILED
        self.save()

    def mark_finished(self):
        self.status = self.FINISHED
        self.save()


class Job(mongoengine.Document):
    """Jobs are container units, holding one or more tasks."""
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    ERRED = "ERRED"
    FINISHED = "FINISHED"
    STATUSES = (
        (QUEUED, "Queued"),
        (PROCESSING, "Processing"),
        (ERRED, "Erred"),
        (FINISHED, "Finished"),
    )

    STANDALONE = "STANDALONE"
    FETCHABLE = "FETCHABLE"
    JOB_TYPES = (
        (STANDALONE, "Standalone"),
        (FETCHABLE, "Fetchable")
    )

    queue_class = rqueue.RedisQueue

    job_id = mongoengine.StringField(required=True,
                                     primary_key=True,
                                     max_length=MD5_LENGTH,
                                     min_length=MD5_LENGTH)
    status = mongoengine.StringField(choices=STATUSES,
                                     required=True,
                                     default=QUEUED,
                                     help_text="Job status.")
    job_type = mongoengine.StringField(choices=JOB_TYPES,
                                       required=True,
                                       help_text="Job type.")
    scheduled = mongoengine.DateTimeField(required=True,
                                          help_text="Start time of the job.")
    updated = mongoengine.DateTimeField(required=True,
                                        help_text="Time of last status update")
    tasks = mongoengine.ListField(mongoengine.ReferenceField(Task),
                                  required=True,
                                  help_text="References to subtasks of job.")
    options = mongoengine.DictField(help_text="Additional(free-form) options.")

    def generate_id(cls, *args):
        """Generate a unique job_id by feeding the hash object with the passed
        in arguments."""
        md5 = hashlib.md5()

        for data in args:
            md5.update(bytes(str(data), 'utf-8'))

        return md5.hexdigest()

    @classmethod
    def create(cls, targets, job_type, **kwargs):
        """Create a new job from the passed in list of target(s).

        :param targets:  Iterable containing URLs or filesystem paths
        :param kwargs:   All kwargs are stored as additional options of the job
        :returns:       ``Job`` instance
        """
        creation_time = datetime.datetime.utcnow()

        # generate job_id from the current time + the passed in targets
        job_id = cls.generate_id(creation_time, *list(targets))

        job = cls(job_id=job_id,
                  job_type=job_type,
                  scheduled=creation_time,
                  updated=creation_time,
                  options=kwargs)

        job.tasks = [Task.create(job_id, t) for t in targets]
        job.save()
        job.schedule()

        return job

    def schedule(self):
        """Schedule the job for processing by a background worker."""
        queue = self.queue_class()
        queue.put({'type': self.job_type, 'id': self.job_id})

    def retry(self):
        """Retry a previously failed job."""
        self.status = self.QUEUED
        self.schedule()

    def mark_processing(self):
        self.status = self.PROCESSING
        self.save()

    def mark_erred(self):
        self.status = self.ERRED
        self.save()

    def mark_finished(self):
        self.status = self.FINISHED
        self.save()
