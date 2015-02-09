# -*- coding: utf-8 -*-
import datetime
import hashlib

import mongoengine

import rqueue


MD5_LENGTH = 32


class Task(mongoengine.Document):
    """Tasks are the smallest unit of work, which contain an exact target (URL)
    that needs to be processed."""
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
                                     help_text='ID of parent Job.')
    url = mongoengine.URLField(required=True,
                               help_text='Target URL.')
    md5 = mongoengine.StringField(max_length=MD5_LENGTH,
                                  min_length=MD5_LENGTH,
                                  help_text='MD5 hexdigest of target URL.')
    title = mongoengine.StringField(help_text='Processed page title.')
    size = mongoengine.IntField(min_value=0,
                                help_text='Size of page in bytes.')
    images = mongoengine.IntField(min_value=0,
                                  help_text='Number of images on the page.')
    timestamp = mongoengine.DateTimeField(help_text='End time of task.')
    status = mongoengine.StringField(choices=STATUSES,
                                     default=QUEUED,
                                     help_text="Job status.")

    @classmethod
    def create(cls, job_id, url):
        """Create a new task from the passed in list of URLs.

        :param job_id:  The string ID of the parent job instance
        :param url:     The target URL that needs to be processed
        :returns:       ``Task`` instance
        """
        task = cls(job_id=job_id, url=url)
        task.save()
        return task


class Job(mongoengine.Document):
    """Jobs are container units, holding one or more tasks."""
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

    queue_class = rqueue.RedisQueue

    job_id = mongoengine.StringField(required=True,
                                     primary_key=True,
                                     max_length=MD5_LENGTH,
                                     min_length=MD5_LENGTH)
    status = mongoengine.StringField(choices=STATUSES,
                                     required=True,
                                     default=QUEUED,
                                     help_text="Job status.")
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
    def create(cls, urls, **kwargs):
        """Create a new job from the passed in list of URLs.

        :param urls:    Iterable containing URLs to be processed
        :param kwargs:  All kwargs are stored as additional options of the job
        :returns:       ``Job`` instance
        """
        creation_time = datetime.datetime.utcnow()

        # generate job_id from the current time + the passed in urls
        job_id = cls.generate_id(creation_time, *list(urls))

        job = cls(job_id=job_id,
                  scheduled=creation_time,
                  updated=creation_time,
                  options=kwargs)

        job.tasks = [Task.create(job_id, url) for url in urls]
        job.save()
        job.schedule()

        return job

    def schedule(self):
        """Schedule the job for processing by a background worker."""
        queue = self.queue_class()
        queue.put({'type': 'job', 'id': self.job_id})

    def retry(self):
        """Retry a previously failed job."""
        self.status = self.QUEUED
        self.schedule()
