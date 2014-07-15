"""
pack.py: package files for transport over Outernet

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import os
import shutil
import zipfile
import hashlib
import logging
import tempfile
import datetime
import urllib.parse as urlparse
from http.client import BadStatusLine

from lib.content_crypto import sign_content

try:
    import simplejson as json
except ImportError:
    import json

from . import __version__ as _version, __author__ as _author
from .fetch import fetch_rendered
from .extract import *


__version__ = _version
__author__ = _author
__all__ = ('zipdir', 'collect', 'BASE_DIR')


COMPRESSION = zipfile.ZIP_DEFLATED
BASE_DIR = tempfile.gettempdir()
TS_FORMAT = '%Y-%m-%d %H:%M:%S UTC'


def zipdir(path, dirpath):
    """ Create a zipball at ``path`` containing the directory at ``dirpath``

    :param path:        Path of the zipball
    :param dirpath:     Path of the directory to zip up
    """
    # Get the path of the directory's parent
    basepath = os.path.dirname(dirpath)

    # Compress all directory contents
    with zipfile.ZipFile(path, 'w', COMPRESSION) as zipball:
        for content in os.listdir(dirpath):
            cpath = os.path.join(dirpath, content)
            if os.path.isdir(cpath):
                continue  # Skip directories
            zipball.write(cpath, os.path.relpath(cpath, basepath))
        zipball.testzip()


def collect(url, keyring=None, key=None, passphrase=None, prep=[], meta={},
            base_dir=BASE_DIR, keep_dir=False):
    """ Collect at ``url`` into a directory within ``base_dir`` and zip it

    The directory is created within ``base_dir`` that is named after the md5
    checksum of the ``identifier``.

    If the target directory already exists, it will be unlinked first.

    :param url:         Identifier for the batch (usually URL of the page)
    :param keyring:     Keyring directory
    :param key:         Key to use for signing
    :param passphrase:  Key passphrase
    :param prep:        Iterable containing HTML preprocessors from
                        ``artexin.preprocessors``
    :param meta:        Document extra metadata
    :param base_dir:    Base directory in which to operate
    :param keep_dir:    Keep the directory in which content was collected
    :returns:           Full path of the newly created zipball
    """

    # Common metadata
    meta.update({
        'url': url,
        'domain': urlparse.urlparse(url)[1]
    })

    # Create the destination directory
    md5 = hashlib.md5()
    md5.update(bytes(url, 'utf-8'))
    checksum = md5.hexdigest()
    dest = os.path.join(base_dir, checksum)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.mkdir(dest)  # FIXME: Handle failure

    # Fetch and prepare the HTML
    try:
        page = fetch_rendered(url)
    except Exception as err:
        # We will trap any exceptions and return a meta object with 'error' key
        # set to exception object. This won't help debugging a whole lot, but
        # it will give us a peek into what went down. We will also log the
        # exception just in case.
        logging.exception('Error %s while processing %s' % (err, url))
        meta.update({
            'timestamp': datetime.datetime.utcnow(),
            'error': str(err),
        })

    timestamp = datetime.datetime.utcnow()
    for preprocessor in prep:
        page = preprocessor(page)
    title, html = extract(page)  # FIXME: Handle failure
    html = strip_links(html)

    # Process images
    html, images = process_images(html, url, imgdir=dest)

    # Write file metadata
    meta.update({
        'timestamp': timestamp.strftime(TS_FORMAT),
        'title': title,
        'images': len(images),
    })
    # FIXME: Handle failure
    with open(os.path.join(dest, 'info.json'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(meta, indent=2))

    # Write the HTML file
    # FIXME: Handle failure
    with open(os.path.join(dest, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)

    # Create a zip file
    zippath = os.path.join(base_dir, '%s.zip' % checksum)
    zipdir(zippath, dest)  # FIXME: Handle failure

    # Clean-up
    if not keep_dir:
        shutil.rmtree(dest)

    stat = os.stat(zippath)

    # Encrypt zip file
    if all([keyring, key, passphrase]):
        signed = sign_content(zippath, keyring, key, passphrase,
                              output_dir=base_dir)
        if not os.path.exists(signed):
            # Python-gnupg will silently fail. It will log a warning, but won't
            # raise any exceptions. The only way to know is to test if the file
            # exists. If the file does not exist, we assume it failed.
            os.unlink(zippath)
            meta.update({
                'timestamp': datetime.datetime.now(),
                'error': "Error signing '%s'" % zippath
            })
            return meta
        os.unlink(zippath)
        zippath = signed

    meta.update({
        'zipfile': zippath,
        'images': len(images),
        'size': stat.st_size,
        'hash': checksum,
        'timestamp': timestamp,  # Pass timestamp as native datetime object
    })

    return meta


if __name__ == '__main__':
    import doctest
    doctest.testmod()
