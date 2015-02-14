# -*- coding: utf-8 -*-
import datetime
import json
import imghdr
import logging
import os
import urllib

from bs4 import BeautifulSoup

from artexin.extract import get_title
from artexin.pack import zipdir, serialize_datetime

from artexinweb import settings, utils
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
        origin = options.get('origin')

        meta = {}
        meta['hash'] = utils.hash_data([origin])
        meta['title'] = self.read_title(task.target)
        meta['images'] = self.count_images(task.target)
        meta['timestamp'] = serialize_datetime(datetime.datetime.utcnow())

        meta['url'] = origin
        meta['domain'] = urllib.parse.urlparse(origin).netloc

        meta_filepath = os.path.join(task.target, 'info.json')
        with open(meta_filepath, 'w', encoding='utf-8') as meta_file:
            meta_file.write(json.dumps(meta, indent=2))

        zip_file_path = os.path.join(settings.BOTTLE_CONFIG['artexin.out_dir'],
                                     '{0}.zip'.format(meta['hash']))
        zipdir(zip_file_path, task.target)

        meta['size'] = os.stat(zip_file_path).st_size

        return meta

    def read_title(self, target):
        is_html_file = lambda filename: any(filename.endswith(ext)
                                            for ext in ('htm', 'html'))
        (html_filename,) = [filename for filename in os.listdir(target)
                            if is_html_file(filename)]

        with open(os.path.join(target, html_filename), 'r') as html_file:
            soup = BeautifulSoup(html_file.read())

        return get_title(soup)

    def count_images(self, target):
        is_image = lambda filename: imghdr.what(os.path.join(target, filename))

        count = 0
        for (dirpath, dirnames, filenames) in os.walk(target):
            count += len([fname for fname in filenames if is_image(fname)])

        return count

    def handle_task_result(self, task, result, options):
        task.size = result['size']
        task.md5 = result['hash']
        task.title = result['title']
        task.images = result['images']
        task.timestamp = result['timestamp']
        task.mark_finished()  # implicit save


@registered(Job.STANDALONE)
def fetchable_handler(job_data):
    handler_instance = StandaloneHandler()
    handler_instance.run(job_data)
