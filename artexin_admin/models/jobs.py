# -*- coding: utf-8 -*-
import datetime
import hashlib

import mongoengine

import rqueue


MD5_LENGTH = 32


class Task(mongoengine.Document):
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


class Job(mongoengine.Document):
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

    @classmethod
    def create(cls, urls, **kwargs):
        """Create a new job from the passed in list of URLs.

        :param urls:    Iterable containing URLs to be processed
        :param kwargs:  All kwargs are stored as additional options of the job
        :returns:       ``Job`` instance
        """
        creation_time = datetime.datetime.utcnow()

        md5 = hashlib.md5()
        add_to_md5 = lambda data: md5.update(bytes(str(data), 'utf-8'))
        # generate job_id md5 from the current time + the passed urls
        add_to_md5(creation_time)
        map(add_to_md5, urls)

        job = cls(job_id=md5.hexdigest(),
                  scheduled=creation_time,
                  updated=creation_time,
                  options=kwargs)

        for url in urls:
            task = Task(job_id=job.job_id, url=url)
            task.save()
            job.tasks.append(task)

        job.save()
        job.schedule()

        return job

    def schedule(self):
        """Schedule the job for processing by a background worker."""
        queue = rqueue.RedisQueue()
        queue.put({'type': 'job', 'id': self.job_id})

    def retry(self):
        """Retry a previously failed job."""
        self.status = self.QUEUED
        self.schedule()
