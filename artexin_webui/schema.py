import os
import time
import hashlib
import logging
from datetime import datetime

import mongoengine as mongo

from artexin.batch import batch

from . import __version__ as _version, __author__ as _author

__version__ = _version
__author__ = _author
__all__ = ('Page', 'Batch',)


MD5LEN = 32


class Page(mongo.Document):
    """ Stores metadata about asset collection belonging to a web page """

    def __init__(self, *args, **kwargs):
        # We use the ``file_path`` property while performing the batch job, in
        # order to avoid having to dig though results list. It's not persisted
        # into the database because the file itself is removed once it's
        # broadcast, rending this information useless.
        self.file_path = kwargs.get('file_path')
        super(Page, self).__init__(*args, **kwargs)

    batch_id = mongo.StringField(
        required=True,
        max_length=MD5LEN,
        min_length=MD5LEN,
        help_text='ID of the batch in which this page was processed')
    url = mongo.URLField(
        required=True,
        help_text='page URL')
    md5 = mongo.StringField(
        required=True,
        primary_key=True,
        max_length=MD5LEN,
        min_length=MD5LEN,
        help_text='MD5 hexdigest of page URL')
    title = mongo.StringField(
        required=True,
        help_text='page title')
    size = mongo.IntField(
        required=True,
        min_value=0,
        help_text='payload size in bytes')
    images = mongo.IntField(
        required=True,
        min_value=0,
        help_text='number of images in the payload')
    timestamp = mongo.DateTimeField(
        required=True,
        help_text='page collection timestamp')

    @property
    def batch(self):
        """ Returns the batch in which the page has been retrieved """
        try:
            return Batch.objects.get(id=self.batch_id)
        except Batch.DoesNotExist:
            return None


class Batch(mongo.Document):
    """ Used to record and report information about batch collection jobs """
    batch_id = mongo.StringField(
        required=True,
        primary_key=True,
        max_length=MD5LEN,
        min_length=MD5LEN)
    urls = mongo.ListField(
        mongo.URLField(),
        required=True,
        help_text='list of all URLs passed to this batch')
    failed = mongo.ListField(
        mongo.URLField(),
        help_text='list of URLs that failed to process')
    started = mongo.DateTimeField(
        required=True,
        help_text='start time of the batch')
    finished = mongo.DateTimeField(
        required=True,
        help_text='end time of the batch')
    pages = mongo.ListField(
        mongo.ReferenceField(Page),
        required=True,
        help_text='references to documents that were creted in this batch')

    @property
    def duration(self):
        """ Returns a timedelta object representing time batch job took """
        return self.finished - self.started

    @staticmethod
    def get_batch_id():
        """ Returns MD5 hexdigest of the current time

        This hash is used as ``batch_id`` which uniquely identifies a single
        batch of pages that are processed in one go as part of a single
        request.
        """
        md5 = hashlib.md5()
        md5.update(bytes(str(time.time()), 'utf-8'))
        return md5.hexdigest()

    @classmethod
    def process_urls(cls, urls, **kwargs):
        """ Process a list of URLs in a batch

        This class method assumes the list has been sanitized and cleaned up by
        the caller, and it does not perform any further cleaning.

        Batch ID is generated and the same ID is assigned to all pages
        collected in this call.

        :param urls:    Iterable containing URLs to be processed in the batch
        :param kwargs:  Any extra keyword arguments passed to ``batch()`` call
        :returns:       List of ``Page`` objects
        """
        # Calling it 'self' for lack of better name
        self = cls(urls=urls, batch_id=cls.get_batch_id(),
                   started=datetime.utcnow())
        logging.info('Started batch job %s at %s with URLs:\n%s' % (
            self.id, self.started, '\n'.join(self.urls)))
        results = batch(urls, **kwargs)  # WARNING: batch() has many children!
        self.finished = datetime.utcnow()
        pages = [Page(batch_id=self.batch_id, url=r['url'], md5=r['hash'],
                      title=r['title'], size=r['size'], images=r['images'],
                      timestamp = r['timestamp'], file_path=r['zipfile'])
                 for r in results
                 if r.get('error') is None]
        for page in pages:
            try:
                page.save()
                self.pages.append(page)
            except mongo.ValidationError as err:
                logging.exception('Error processing page %s: %s' % (
                    page.url, err))
                # Invalid data, cannot save
                if os.path.exists(page.file_path):
                    # Remove the zip file
                    logging.debug('Removing zip file %s' % page.file_path)
                    os.unlink(page.file_path)
                self.failed.append(page.url)
        self.save()
        return self
